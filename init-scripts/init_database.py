from models import AIModel, User, Repository, Operation, Agent, UserSettings, CostHistory
from infra.database import Database
from helpers.enums import AIModelProvider, AgentFunction, AgentResponseLength


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
    users = [
        User(
            id = 1,
            provider = "GITHUB",
            provider_id = "nnnnnnnn",
            name = "nome",
            email = "email@gmail.com",
            created_at = "2025-05-14 23:32:56.627",
            updated_at = "2025-05-14 23:32:56.627",
            deleted = False
        )
    ]

    return users

def generate_user_settings():
    user_settings = [
        UserSettings(
            id=1,
            user_id=1,
            email_notifications=True,
            telegram_notifications=False,
            telegram_chat_id="",
            daily_limit=5,
            weekly_limit=25,
            monthly_limit=100,
            alert_threshold=80,
            daily_limit_action="notify_only",
            weekly_limit_action="notify_only",
            monthly_limit_action="disable_agents"
        )
    ]

    return user_settings

def generate_repositories():

    repositories = [
        Repository(
            id = 1,
            user_id = 1,
            created_at = "2025-05-14 23:32:56.627",
            created_by_id = 1,
            updated_at = "2025-05-14 23:32:56.627",
            updated_by_id = 1,
            deleted = False
        )
    ]

    return repositories

# so da certo se trocar no model.py function e response_length para Strings
def generate_agents():
    agents = [
        Agent(
            id = 1,
            name = "roberto",
            function = "pr_review",
            repository_id = 1,
            ai_model_id = 1,
            active = True,
            response_length = "medium",
            created_by_id = 1,
            created_at = "2025-05-14 23:32:56.627",
            updated_by_id = 1,
            updated_at = "2025-05-14 23:32:56.627",
            deleted = False
        )
    ]

    return agents

def generate_operations():
    operations = [
        Operation(
            id = 1,
            agent_id = 1,
            action = "pr_review",
            details = "xxxx",
            github_reference = "xxxx",
            prompt_tokens = 100,
            completion_tokens = 100,
            total_tokens = 200,
            cost = 300.5,
            status = "pending",
            execution_time = 2.04,
            created_at = "2025-05-14 23:32:56.627"
        )
    ]
    return operations

def generate_cost_histories():
    cost_history = [
        CostHistory(
            id = 1,
            user_id =1,
            month = "2025-05",
            pr_cost = 50,
            issue_cost = 50,
            total_cost = 50,
            created_at = "2025-05-14 23:32:56.627"
        )
    ]

    return cost_history

if __name__ == "__main__":
    db = Database()
    db.drop_all()
    db.create_all()
    print("Database tables created successfully.")

    session = db.get_session()
    models = generate_models()
    users = generate_users()
    settings = generate_user_settings()
    repositories = generate_repositories()
    agents = generate_agents()
    operations = generate_operations()
    cost_histories = generate_cost_histories()
    session.add_all(models)
    session.add_all(users)
    session.add_all(settings)
    session.add_all(repositories)
    session.add_all(agents)
    session.add_all(operations)
    session.add_all(cost_histories)
    session.commit()
    db.close_session()
    print("Models inserted successfully.")
