import json
import traceback

from datetime import datetime, UTC
from typing import Dict, Any, List, Tuple

import requests
from openai import OpenAI
from anthropic import Anthropic

from entities.entities import Agent, AIModel, Operation
from helpers.enums import AgentFunction, AgentResponseLength, AIModelProvider, WebhookEventType


class GitHubAIAgent:
    """
    Classe responsável por administrar análises e respostas de IA para eventos do GitHub
    """

    def __init__(self, github_token: str, openai_api_key: str = None, anthropic_api_key: str = None):
        self.github_token = github_token
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key

    def process_github_event(self, event_data: Dict[str, Any], agent: Agent) -> Operation:
        """
        Processa um evento do GitHub (issue ou pull request) e gera uma resposta de IA

        Args:
            event_data: Dados do evento recebido do webhook do GitHub
            agent: Instância do agente configurado

        Returns:
            Operation: Registro da operação executada
        """
        event_type = None
        try:
            event_type = self._identify_event_type(event_data)

            if not self._can_process_event(agent.function, event_type):
                raise ValueError(f"Agente não configurado para processar eventos do tipo {event_type.value}")

            context = self._extract_event_context(event_data, event_type)

            prompt = self._generate_prompt(context, event_type, agent.response_length)

            ai_response, tokens_used, cost = self._call_ai_model(
                prompt, agent.ai_model, context
            )

            github_reference = self._post_github_response(
                event_data, ai_response, event_type
            )

            operation = Operation(
                agent_id=agent.id,
                action=f"{event_type.value}_analysis",
                details=json.dumps({
                    "event_action": event_data.get("action"),
                    "repository": context.get("repository_name"),
                    "number": context.get("number")
                }),
                github_reference=github_reference,
                prompt_tokens=tokens_used.get("prompt_tokens", 0),
                completion_tokens=tokens_used.get("completion_tokens", 0),
                total_tokens=tokens_used.get("total_tokens", 0),
                cost=cost,
                status="completed",
                created_at=datetime.now(UTC)
            )

            return operation

        except Exception as e:
            operation = Operation(
                agent_id=agent.id,
                action=f"{event_type.value}_analysis" if 'event_type' in locals() else "unknown_analysis",
                details=json.dumps({"error": str(e)}),
                cost=0.0,
                status="failed",
                created_at=datetime.now(UTC)
            )
            return operation

    @staticmethod
    def _identify_event_type(event_data: Dict[str, Any]) -> WebhookEventType:
        """Identifica o tipo de evento baseado nos dados recebidos"""
        if "pull_request" in event_data:
            return WebhookEventType.PULL_REQUEST
        elif "issue" in event_data:
            return WebhookEventType.ISSUE
        else:
            raise ValueError("Tipo de evento não suportado")

    @staticmethod
    def _can_process_event(agent_function: AgentFunction, event_type: WebhookEventType) -> bool:
        """Verifica se o agente pode processar o tipo de evento"""
        if agent_function == AgentFunction.BOTH:
            return True
        elif agent_function == AgentFunction.PR_REVIEW and event_type == WebhookEventType.PULL_REQUEST:
            return True
        elif agent_function == AgentFunction.ISSUE_RESOLUTION and event_type == WebhookEventType.ISSUE:
            return True
        return False

    def _extract_event_context(self, event_data: Dict[str, Any], event_type: WebhookEventType) -> Dict[str, Any]:
        """Extrai informações relevantes do evento para análise"""
        context = {
            "repository_name": event_data["repository"]["full_name"],
            "action": event_data.get("action"),
        }

        if event_type == WebhookEventType.PULL_REQUEST:
            pr = event_data["pull_request"]
            context.update({
                "number": pr["number"],
                "title": pr["title"],
                "body": pr["body"] or "",
                "author": pr["user"]["login"],
                "base_branch": pr["base"]["ref"],
                "head_branch": pr["head"]["ref"],
                "changed_files": pr.get("changed_files", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "url": pr["html_url"]
            })

            context["code_changes"] = self._get_pr_code_changes(context["repository_name"], pr["number"])
            context["files_changed"] = self._get_pr_files_list(context["repository_name"], pr["number"])

        elif event_type == WebhookEventType.ISSUE:
            issue = event_data["issue"]
            context.update({
                "number": issue["number"],
                "title": issue["title"],
                "body": issue["body"] or "",
                "author": issue["user"]["login"],
                "labels": [label["name"] for label in issue.get("labels", [])],
                "state": issue["state"],
                "url": issue["html_url"]
            })

            context["relevant_code"] = self._get_issue_relevant_code(context["repository_name"], issue)

        return context

    @staticmethod
    def _generate_prompt(
            context: Dict[str, Any],
            event_type: WebhookEventType,
            response_length: AgentResponseLength
    ) -> str:
        """Gera o prompt para a IA baseado no contexto e configurações"""

        length_instructions = {
            AgentResponseLength.CONCISE: "Seja conciso e direto ao ponto, com no máximo 3 parágrafos.",
            AgentResponseLength.MEDIUM: "Forneça uma análise moderadamente detalhada, com 4-6 parágrafos.",
            AgentResponseLength.DETAILED: "Forneça uma análise completa e detalhada, explorando todos os aspectos relevantes."
        }

        length_instruction = length_instructions[response_length]

        if event_type == WebhookEventType.PULL_REQUEST:
            return f"""
Como um revisor especializado de código, analise o seguinte Pull Request:

**Repositório:** {context['repository_name']}
**PR #{context['number']}:** {context['title']}
**Autor:** {context['author']}
**Branch:** {context['head_branch']} → {context['base_branch']}
**Alterações:** {context['changed_files']} arquivos, +{context['additions']} -{context['deletions']} linhas

**Descrição:**
{context['body']}

**Arquivos Modificados:**
{chr(10).join([f"- {file['filename']} (+{file['additions']} -{file['deletions']})" for file in context.get('files_changed', [])])}

**Mudanças de Código:**
{context.get('code_changes', 'Não foi possível recuperar as mudanças de código.')}

Por favor, forneça uma análise que inclua:
1. **Resumo da análise:** Visão geral das mudanças propostas
2. **Análise do código:** Qualidade, padrões e boas práticas
3. **Pontos positivos:** O que está bem implementado
4. **Sugestões de melhoria:** Aspectos que podem ser aprimorados (código, estrutura, performance)
5. **Considerações de segurança:** Possíveis vulnerabilidades ou riscos
6. **Testes:** Verificar se há testes adequados para as mudanças
7. **Recomendação:** Se deve ser aprovado, aprovado com ressalvas, ou rejeitado

{length_instruction}

Use um tom profissional e construtivo. Formate sua resposta em Markdown.
"""

        # elif event_type == WebhookEventType.ISSUE:
        else:
            return f"""
Como um assistente especializado em análise de issues, analise a seguinte issue:

**Repositório:** {context['repository_name']}
**Issue #{context['number']}:** {context['title']}
**Autor:** {context['author']}
**Estado:** {context['state']}
**Labels:** {', '.join(context['labels']) if context['labels'] else 'Nenhuma'}

**Descrição:**
{context['body']}

**Código Relacionado:**
{context.get('relevant_code', 'Nenhum código específico identificado.')}

Por favor, forneça uma análise que inclua:
1. **Classificação:** Tipo de issue (bug, feature request, documentação, etc.)
2. **Prioridade sugerida:** Baseada na descrição e impacto
3. **Análise técnica:** Aspectos técnicos relevantes baseados no código
4. **Possível causa raiz:** Se for um bug, análise do que pode estar causando
5. **Sugestões de solução:** Possíveis abordagens para resolver, incluindo exemplos de código se necessário
6. **Estimativa de complexidade:** Simples, médio ou complexo
7. **Próximos passos:** Recomendações específicas para o desenvolvimento

{length_instruction}

Use um tom profissional e prestativo. Formate sua resposta em Markdown.
"""

    def _call_ai_model(self, prompt: str, ai_model: AIModel, context: Dict[str, Any]) -> Tuple[
        str, Dict[str, int], float]:
        """Chama o modelo de IA configurado (OpenAI ou Anthropic)"""
        if ai_model.provider == AIModelProvider.OPENAI:
            return self._call_openai(prompt, ai_model, context)
        elif ai_model.provider == AIModelProvider.ANTHROPIC:
            return self._call_anthropic(prompt, ai_model, context)
        else:
            raise ValueError(f"Provedor de IA {ai_model.provider} não suportado")

    def _call_openai(self, prompt: str, ai_model: AIModel, context: Dict[str, Any]) -> Tuple[
        str, Dict[str, int], float]:
        """Chama a API da OpenAI usando a biblioteca oficial"""

        # Obter response_length do contexto
        agent_config = context.get('_agent_config', {})
        response_length = agent_config.get('response_length', AgentResponseLength.MEDIUM)

        # Configurar max_tokens baseado no response_length
        max_tokens = None
        if response_length == AgentResponseLength.CONCISE:
            max_tokens = 2000  # Ajustado para valor mais realista
        elif response_length == AgentResponseLength.MEDIUM:
            max_tokens = 4000
        # DETAILED não define max_tokens (usa o padrão do modelo)

        try:
            # Fazer chamada para a API
            completion = OpenAI(api_key=self.openai_api_key).chat.completions.create(
                model=ai_model.name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=max_tokens
            )

            # Extrair resposta
            content = completion.choices[0].message.content

            # Calcular custos
            usage = completion.usage
            prompt_cost = usage.prompt_tokens * ai_model.prompt_token_cost / 1000
            completion_cost = usage.completion_tokens * ai_model.completion_token_cost / 1000
            total_cost = prompt_cost + completion_cost

            # Retornar no formato esperado
            tokens_used = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens
            }

            return content, tokens_used, total_cost

        except Exception as e:
            raise Exception(f"Erro ao chamar OpenAI API: {str(e)}")

    def _call_anthropic(self, prompt: str, ai_model: AIModel, context: Dict[str, Any]) -> Tuple[
        str, Dict[str, int], float]:
        """Chama a API da Anthropic usando a biblioteca oficial"""

        # Obter response_length do contexto
        agent_config = context.get('_agent_config', {})
        response_length = agent_config.get('response_length', AgentResponseLength.MEDIUM)

        # Configurar max_tokens baseado no response_length
        max_tokens = 4096  # Padrão
        if response_length == AgentResponseLength.CONCISE:
            max_tokens = 2000
        elif response_length == AgentResponseLength.MEDIUM:
            max_tokens = 4000
        # DETAILED usa o máximo permitido (4096)

        try:
            # Fazer chamada para a API
            message = Anthropic(api_key=self.anthropic_api_key).messages.create(
                model=ai_model.name,
                max_tokens=max_tokens,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extrair resposta
            content = message.content[0].text

            # Calcular custos
            prompt_tokens = message.usage.input_tokens
            completion_tokens = message.usage.output_tokens
            total_tokens = prompt_tokens + completion_tokens

            prompt_cost = prompt_tokens * ai_model.prompt_token_cost
            completion_cost = completion_tokens * ai_model.completion_token_cost
            total_cost = prompt_cost + completion_cost

            # Retornar no formato esperado
            tokens_used = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }

            return content, tokens_used, total_cost

        except Exception as e:
            raise Exception(f"Erro ao chamar Anthropic API: {str(e)}")

    def _post_github_response(self, event_data: Dict[str, Any], ai_response: str,
                                    event_type: WebhookEventType) -> str:
        """Posta a resposta da IA no GitHub como comentário"""

        repo_full_name = event_data["repository"]["full_name"]

        if event_type == WebhookEventType.PULL_REQUEST:
            number = event_data["pull_request"]["number"]
            url = f"https://api.github.com/repos/{repo_full_name}/issues/{number}/comments"
        elif event_type == WebhookEventType.ISSUE:
            number = event_data["issue"]["number"]
            url = f"https://api.github.com/repos/{repo_full_name}/issues/{number}/comments"

        formatted_response = f"{ai_response}\n\n---\n*Análise gerada automaticamente por IA* 🤖"

        response = requests.post(
            url,
            headers={
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={"body": formatted_response}
        )

        response.raise_for_status()
        comment_data = response.json()

        return comment_data["html_url"]

    def _get_pr_code_changes(self, repo_full_name: str, pr_number: int) -> str:
        """Busca as mudanças de código do Pull Request"""
        try:
            response = requests.get(
                f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3.diff"
                }
            )

            if response.status_code == 200:
                diff_content = response.text
                if len(diff_content) > 15000:  # ~15k caracteres
                    return diff_content[:15000] + "\n\n... (diff truncado devido ao tamanho)"
                return diff_content
            else:
                return "Não foi possível recuperar as mudanças de código."

        except Exception as e:
            return f"Erro ao buscar mudanças: {str(e)}"

    def _get_pr_files_list(self, repo_full_name: str, pr_number: int) -> List[Dict[str, Any]]:
        """Busca a lista de arquivos modificados no PR"""
        try:
            response = requests.get(
                f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )

            if response.status_code == 200:
                files = response.json()
                return [{
                    "filename": file["filename"],
                    "status": file["status"],
                    "additions": file["additions"],
                    "deletions": file["deletions"],
                    "changes": file["changes"]
                } for file in files]
            else:
                return []

        except Exception:
            traceback.print_exc()
            return []

    def _get_issue_relevant_code(self, repo_full_name: str, issue: Dict[str, Any]) -> str:
        """Tenta identificar e buscar código relevante para a issue"""
        try:
            import re

            issue_text = f"{issue['title']} {issue['body'] or ''}"

            file_patterns = [
                r'`([^`]+\.[a-zA-Z]+)`',
                r'([a-zA-Z_][a-zA-Z0-9_/]*\.[a-zA-Z]+)',
                r'src/([a-zA-Z0-9_/]+\.[a-zA-Z]+)',
                r'([a-zA-Z0-9_]+\.py)',
                r'([a-zA-Z0-9_]+\.js)',
                r'([a-zA-Z0-9_]+\.java)',
            ]

            potential_files = []
            for pattern in file_patterns:
                matches = re.findall(pattern, issue_text, re.IGNORECASE)
                potential_files.extend(matches)

            potential_files = list(set(potential_files))
            potential_files = [f for f in potential_files if len(f) > 3 and not f.startswith('http')]

            if not potential_files:
                return "Nenhum arquivo específico mencionado na issue."

            code_snippets = []

            for file_path in potential_files[:3]:
                try:
                    response = requests.get(
                        f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}",
                        headers={
                            "Authorization": f"token {self.github_token}",
                            "Accept": "application/vnd.github.v3+json"
                        }
                    )

                    if response.status_code == 200:
                        file_data = response.json()
                        if file_data.get("encoding") == "base64":
                            import base64
                            content = base64.b64decode(file_data["content"]).decode('utf-8')

                            # Limita o tamanho do arquivo
                            if len(content) > 5000:
                                content = content[:5000] + "\n... (arquivo truncado)"

                            code_snippets.append(f"**{file_path}:**\n```\n{content}\n```")

                except Exception:
                    continue

            if code_snippets:
                return "\n\n".join(code_snippets[:2])
            else:
                return f"Arquivos mencionados: {', '.join(potential_files[:5])}, mas não foi possível recuperar o conteúdo."

        except Exception as e:
            return f"Erro ao analisar código relacionado: {str(e)}"
