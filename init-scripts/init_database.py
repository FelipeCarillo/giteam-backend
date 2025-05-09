from models import AIModel, User, UserSettings, Operation, CostHistory, Agent, Repository
from infra.database import Database
from helpers.enums import AIModelProvider, AuthProvider, AgentFunction, AgentResponseLength
from datetime import datetime, UTC, timedelta
import uuid


def generate_models():
    ai_models = [
        AIModel(
            name="gpt-4o",
            provider=AIModelProvider.OPENAI,
            specialties_us="Ideal for reviewing large codebases, suggesting improvements and optimizations, identifying complex errors, and offering solutions to high-level issues in code.",
            specialties_br="Ideal para revisar grandes bases de código, sugerir melhorias e otimizações, identificar erros complexos e oferecer soluções para problemas de alto nível no código.",
            prompt_token_cost=2.5 / 1_000_000,
            completion_token_cost=10 / 1_000_000,
            active=True
        ),
        AIModel(
            name="gpt-4o-mini",
            provider=AIModelProvider.OPENAI,
            specialties_us="Efficient at quickly reviewing small code snippets, suggesting improvements, and fixing common issues, making it ideal for fast and simple pull request reviews with low volume.",
            specialties_br="Eficiente em revisar rapidamente pequenos trechos de código, sugerir melhorias e corrigir problemas comuns, tornando-o ideal para revisões rápidas e simples de pull requests com baixo volume.",
            prompt_token_cost=0.15 / 1_000_000,
            completion_token_cost=0.6 / 1_000_000,
            active=True
        ),
        AIModel(
            name="gpt-4.1",
            provider=AIModelProvider.OPENAI,
            specialties_us="Excellent for logical reasoning, problem-solving, and generating code, providing advanced performance in technical contexts and development, especially for complex coding issues and algorithm design.",
            specialties_br="Excelente para raciocínio lógico, resolução de problemas e geração de código, oferecendo desempenho avançado em contextos técnicos e desenvolvimento, especialmente para questões complexas de codificação e design de algoritmos.",
            prompt_token_cost=2 / 1_000_000,
            completion_token_cost=8 / 1_000_000,
            active=True
        ),
        AIModel(
            name="claude-3.7-sonnet",
            provider=AIModelProvider.ANTHROPIC,
            specialties_us="While primarily artistic, this model can generate creative solutions for code comments, documentation, and generating poetic-style code documentation or creative descriptions in issues or pull requests.",
            specialties_br="Embora seja principalmente artístico, este modelo pode gerar soluções criativas para comentários de código, documentação e gerar documentação de código ou descrições criativas em estilo poético em problemas ou pull requests.",
            prompt_token_cost=3 / 1_000_000,
            completion_token_cost=15 / 1_000_000,
            active=True
        ),
        AIModel(
            name="claude-3.5-haiku",
            provider=AIModelProvider.ANTHROPIC,
            specialties_us="Best for short and concise code documentation, creating brief summaries of code changes in a poetic, minimalist style, or generating creative, condensed issue descriptions or pull request summaries.",
            specialties_br="Melhor para documentação de código curta e concisa, criando resumos breves de alterações de código em um estilo poético e minimalista, ou gerando descrições criativas e condensadas de problemas ou resumos de pull requests.",
            prompt_token_cost=0.8 / 1_000_000,
            completion_token_cost=4 / 1_000_000,
            active=True
        )
    ]

    return ai_models


def generate_users():
    """Gera usuários de exemplo para o banco de dados."""
    users = [
        User(
            provider=AuthProvider.GITHUB,
            provider_id=str(uuid.uuid4()),
            name="Admin User",
            email="admin@giteam.com",
            deleted=False
        ),
        User(
            provider=AuthProvider.GITHUB,
            provider_id=str(uuid.uuid4()),
            name="Test User",
            email="test@giteam.com",
            deleted=False
        ),
        User(
            provider=AuthProvider.GITHUB,
            provider_id=str(uuid.uuid4()),
            name="Developer User",
            email="dev@giteam.com",
            deleted=False
        )
    ]

    return users


def generate_user_settings(users):
    """Gera configurações de usuário para os usuários de exemplo."""
    user_settings = []

    for user in users:
        settings = UserSettings(
            user_id=user.id,
            email_notifications=True,
            telegram_notifications=False,
            daily_limit=5.0,
            weekly_limit=25.0,
            monthly_limit=100.0,
            alert_threshold=80,
            daily_limit_action='notify_only',
            weekly_limit_action='notify_only',
            monthly_limit_action='disable_agents'
        )
        user_settings.append(settings)

    return user_settings


def generate_repositories(users):
    """Gera repositórios de exemplo para o banco de dados."""
    repositories = []

    for user in users:
        repositories.append(
            Repository(
                user_id=user.id,
                created_by_id=user.id,
                updated_by_id=user.id,
                deleted=False
            )
        )

    return repositories


def generate_agents(users, repositories, ai_models):
    """Gera agentes de exemplo para o banco de dados."""
    agents = []

    # Vamos criar um agente para cada combinação de usuário e repositório
    for user in users:
        for repo in repositories:
            for i, model in enumerate(ai_models[:2]):  # Usamos apenas os dois primeiros modelos para simplicidade
                function = AgentFunction.PR_REVIEW if i % 2 == 0 else AgentFunction.ISSUE_RESOLUTION
                agents.append(
                    Agent(
                        name=f"Agent {function.value} for {user.name}",
                        function=function,
                        repository_id=repo.id,
                        ai_model_id=model.id,
                        active=True,
                        response_length=AgentResponseLength.MEDIUM,
                        created_by_id=user.id,
                        updated_by_id=user.id,
                        deleted=False
                    )
                )

    return agents


def generate_operations(agents):
    """Gera operações de exemplo para o banco de dados."""
    operations = []

    for agent in agents:
        # Para cada agente, criamos algumas operações de exemplo
        operations.extend([
            Operation(
                agent_id=agent.id,
                action=agent.function.value,
                details=f"{agent.function.value} for project X",
                github_reference="PR#123" if agent.function == AgentFunction.PR_REVIEW else "Issue#456",
                prompt_tokens=1500,
                completion_tokens=500,
                total_tokens=2000,
                cost=0.05,
                status="completed",
                execution_time=2.5,
                created_at=datetime.now(UTC) - timedelta(days=5)
            ),
            Operation(
                agent_id=agent.id,
                action=agent.function.value,
                details=f"{agent.function.value} for project Y",
                github_reference="PR#124" if agent.function == AgentFunction.PR_REVIEW else "Issue#457",
                prompt_tokens=2000,
                completion_tokens=800,
                total_tokens=2800,
                cost=0.07,
                status="completed",
                execution_time=3.2,
                created_at=datetime.now(UTC) - timedelta(days=3)
            )
        ])

    return operations


def generate_cost_history(users):
    """Gera histórico de custos para os usuários de exemplo."""
    cost_history = []

    current_date = datetime.now(UTC)
    current_month = current_date.strftime("%Y-%m")
    previous_month = (current_date - timedelta(days=30)).strftime("%Y-%m")

    for user in users:
        cost_history.extend([
            CostHistory(
                user_id=user.id,
                month=current_month,
                pr_cost=2.50,
                issue_cost=1.75,
                total_cost=4.25,
                created_at=current_date
            ),
            CostHistory(
                user_id=user.id,
                month=previous_month,
                pr_cost=3.25,
                issue_cost=2.10,
                total_cost=5.35,
                created_at=current_date
            )
        ])

    return cost_history


if __name__ == "__main__":
    db = Database()
    db.drop_all()
    db.create_all()
    print("Database tables created successfully.")

    session = db.get_session()

    # Inserir modelos de IA
    models = generate_models()
    session.add_all(models)
    session.commit()
    print("AI Models inserted successfully.")

    # Inserir usuários
    users = generate_users()
    session.add_all(users)
    session.commit()
    print("Users inserted successfully.")

    # Inserir configurações de usuário
    user_settings = generate_user_settings(users)
    session.add_all(user_settings)
    session.commit()
    print("User Settings inserted successfully.")

    # Inserir repositórios
    repositories = generate_repositories(users)
    session.add_all(repositories)
    session.commit()
    print("Repositories inserted successfully.")

    # Inserir agentes
    agents = generate_agents(users, repositories, models)
    session.add_all(agents)
    session.commit()
    print("Agents inserted successfully.")

    # Inserir operações
    operations = generate_operations(agents)
    session.add_all(operations)
    session.commit()
    print("Operations inserted successfully.")

    # Inserir histórico de custos
    cost_history = generate_cost_history(users)
    session.add_all(cost_history)
    session.commit()
    print("Cost History inserted successfully.")

    db.close_session()
    print("Database initialization completed.")