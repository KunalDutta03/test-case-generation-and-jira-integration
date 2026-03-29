import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field("2024-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment_name: str = Field("gpt-4.1-2", env="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_embedding_deployment: str = Field("text-embedding-3-large", env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    azure_openai_embedding_endpoint: str = Field(..., env="AZURE_OPENAI_EMBEDDING_ENDPOINT")

    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_ssl_mode: str = Field("require", env="DB_SSL_MODE")

    # Jira
    jira_base_url: str = Field("", env="JIRA_BASE_URL")
    jira_email: str = Field("", env="JIRA_EMAIL")
    jira_api_token: str = Field("", env="JIRA_API_TOKEN")
    jira_default_project_key: str = Field("QA", env="JIRA_DEFAULT_PROJECT_KEY")
    jira_default_issue_type: str = Field("Task", env="JIRA_DEFAULT_ISSUE_TYPE")

    # App
    app_secret_key: str = Field("changeme", env="APP_SECRET_KEY")
    app_environment: str = Field("development", env="APP_ENVIRONMENT")
    app_cors_origins: str = Field("http://localhost:5173", env="APP_CORS_ORIGINS")
    app_log_level: str = Field("INFO", env="APP_LOG_LEVEL")
    upload_max_size_mb: int = Field(50, env="UPLOAD_MAX_SIZE_MB")
    upload_dir: str = Field("./uploads", env="UPLOAD_DIR")
    faiss_index_path: str = Field("./faiss_index", env="FAISS_INDEX_PATH")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
