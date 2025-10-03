import enum
import logging
import os
from pydantic_settings import BaseSettings
from yarl import URL
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(override=True)

class LogLevel(str, enum.Enum):
    """Possible log levels."""
    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class ApplicationSettings(BaseSettings):
    """Application-specific settings."""
    host: str = "0.0.0.0"
    port: int = int(os.environ.get("PORT", "8090"))
    workers_count: int = 3
    reload: bool = True
    environment: str = os.environ.get("ENVIRONMENT", "NAL-PLATFORM")
    log_level: str = os.environ.get("LOG_LEVEL", "DEBUG")
    app_title: str = "NAL Platform Service"
    app_version: str = "0.1.0"
    logging_environment: str = os.environ.get("LOGGING_ENVIRONMENT", "dev")
    jwt_secret: str = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
    jwt_algorithm: str = os.environ.get("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    class Config:
        env_prefix = "APP_"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    POSTGRES_DB_PORT: str | None = os.environ.get("POSTGRES_DB_PORT", "5432")
    POSTGRES_DB_NAME: str | None = os.environ.get("POSTGRES_DB_NAME", "alstonair_db")
    POSTGRES_DB_PASSWORD: str | None = os.environ.get("POSTGRES_DB_PASSWORD", "password")
    POSTGRES_DB_USERNAME: str | None = os.environ.get("POSTGRES_DB_USERNAME", "postgres")
    POSTGRES_DB_HOST: str | None = os.environ.get("POSTGRES_DB_HOST", "localhost")
    POSTGRES_SCHEMA_NAME: str | None = os.environ.get("POSTGRES_SCHEMA_NAME")

    @property
    def url(self) -> URL:
        """Assemble database URL from settings."""
        return URL.build(
            scheme="postgresql+asyncpg",
            host=self.POSTGRES_DB_HOST,
            port=int(self.POSTGRES_DB_PORT) if self.POSTGRES_DB_PORT else 5432,
            user=self.POSTGRES_DB_USERNAME,
            password=self.POSTGRES_DB_PASSWORD,
            path=f"/{self.POSTGRES_DB_NAME}",
        )

    class Config:
        env_prefix = "DB_"

class AzureSettings(BaseSettings):
    """Azure configuration settings."""
    api_key: str | None = os.environ.get("api_key")
    api_version: str | None = os.environ.get("AZURE_API_VERSION")
    endpoint: str | None = os.environ.get("AZURE_ENDPOINT")
    deployment: str | None = os.environ.get("AZURE_DEPLOYMENT")
    deployment_4o: str | None = os.environ.get('AZURE_DEPLOYMENT_4O')
    model_4o: str | None = os.environ.get('AZURE_DEPLOYMENT_MODEL_4O')
    embedding_deployment: str | None = os.environ.get('AZURE_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
    openai_embeddings_deployment: str | None = os.environ.get('OPENAI_EMBEDDINGS_DEPLOYMENT')
    tenant_id: str | None = os.environ.get('TENANT_ID')
    client_id: str | None = os.environ.get('CLIENT_ID')
    client_secret: str | None = os.environ.get('CLIENT_SECRET')
    service_bus_namespace: str | None = os.environ.get('SERVICE_BUS_NAMESPACE')
    service_bus_key: str | None = os.environ.get("SERVICE_BUS_KEY")
    development_version: str | None = os.environ.get('AZURE_DEPLOYMENT_4O_VERSION')
    redis_password: str | None= os.environ.get('REDIS_PASSWORD')

    class Config:
        env_prefix = "AZURE_"

class GCPSettings(BaseSettings):
    """Google Cloud Platform configuration settings."""
      # Default from backup
    region: str | None = os.environ.get('REGION', 'us-west1')  # Default from backup
    bucket_name: str | None = os.environ.get('GCS_BUCKET_NAME')
    service_account_path: str | None = None  # Path to service account JSON file
    vertexai_region: str | None = os.environ.get('VERTEXAI_REGION')
    index_id: str | None = os.environ.get('INDEX_ID')
    endpoint_id: str | None = os.environ.get('ENDPOINT_ID')
    model_326: str | None = os.environ.get('GCP_MODEL_326')
    model_331: str | None = os.environ.get('GCP_MODEL_331')
    model_391: str | None = os.environ.get('GCP_MODEL_391')
    explainer_326: str | None = os.environ.get('GCP_EXPLAINER_326')
    explainer_331: str | None = os.environ.get('GCP_EXPLAINER_331')
    explainer_391: str | None = os.environ.get('GCP_EXPLAINER_391')
    model_api_endpoint: str | None = os.environ.get('MODEL_API_ENDPOINT')
    
    # GCP Service Account components
    google_type: str | None = os.environ.get('GOOGLE_TYPE')
    google_project_id: str | None = os.environ.get('PROJECT_ID')
    google_private_key_id: str | None = os.environ.get('GOOGLE_PRIVATE_KEY_ID')
    google_private_key: str | None = os.environ.get('GOOGLE_PRIVATE_KEY')
    google_client_email: str | None = os.environ.get('GOOGLE_CLIENT_EMAIL')
    google_client_id: str | None = os.environ.get('GOOGLE_CLIENT_ID')
    google_auth_uri: str | None = os.environ.get('GOOGLE_AUTH_URI')
    google_token_uri: str | None = os.environ.get('GOOGLE_TOKEN_URI')
    google_auth_provider_x509_cert_url: str | None = os.environ.get('GOOGLE_AUTH_PROVIDER_X509_CERT_URL')
    google_client_x509_cert_url: str | None = os.environ.get('GOOGLE_CLIENT_X509_CERT_URL')
    google_universe_domain: str | None = os.environ.get('GOOGLE_UNIVERSE_DOMAIN')
    project_id_video: str | None = os.environ.get('PROJECT_ID_VIDEO')
    topic_id_video: str | None = os.environ.get('TOPIC_ID_VIDEO')
    video_scripts_to_create: str | None = os.environ.get('VIDEO_SCRIPTS_TO_CREATE')
    # New config for GuestPulse
    guestpulse_labelencode_endpoint_id: str | None = os.environ.get('GuestPulse_LabelEncode_ENDPOINT_ID')
    guestpulse_xgboost_endpoint_id: str | None = os.environ.get('GuestPulse_XGB_ENDPOINT_ID')
    guestpulse_prophet_endpoint_id: str | None = os.environ.get('GuestPulse_Prophet_Endpoint_id')
    guestpulse_req_url: str | None = os.environ.get('GuestPulse_requrl')
    
    class Config:
        env_prefix = "GCP_"

class DatabricksSettings(BaseSettings):
    """Databricks configuration settings."""
    data_bricks_endpoint_name: str | None = os.environ.get('DATABRICKS_ENDPOINT_NAME')
    data_bricks_endpoint_gcp_name:str | None = os.environ.get('DATABRICKS_ENDPOINT_GCP_NAME')
    base_schema: str | None = os.environ.get('DATABRICKS_BASE_SCHEMA')
    base_gcp_schema:str | None = os.environ.get('DATABRICKS_BASE_GCP_SCHEMA')
    data_bricks_host: str | None = os.environ.get('DATABRICKS_HOST')
    data_bricks_token: str | None = os.environ.get('DATABRICKS_TOKEN')
    data_bricks_model_326: str | None = os.environ.get('DATABRICKS_MODEL_326')
    data_bricks_model_331: str | None = os.environ.get('DATABRICKS_MODEL_331')
    data_bricks_model_391: str | None = os.environ.get('DATABRICKS_MODEL_391')
    data_bricks_explainer_326: str | None = os.environ.get('DATABRICKS_EXPLAINER_326')
    data_bricks_explainer_331: str | None = os.environ.get('DATABRICKS_EXPLAINER_331')
    data_bricks_explainer_391: str | None = os.environ.get('DATABRICKS_EXPLAINER_391')
    data_bricks_endpoint_dynamic_name: str | None = os.environ.get('DATABRICKS_ENDPOINT_DYNAMIC_NAME')

    class Config:
        env_prefix = "DATABRICKS_"

class AISettings(BaseSettings):
    """AI/ML model configuration settings."""
    llm_model_name: str | None = os.environ.get('LLM_MODEL_NAME')
    model_name: str | None = os.environ.get('MODEL_NAME')
    image_model_name: str | None = os.environ.get('IMAGE_MODEL_NAME')
    llm_image_model_name: str | None = os.environ.get('LLM_IMAGE_MODEL_NAME')
    total_images: int = int(os.environ.get('TOTAL_IMAGES', '2'))
    milvus_host: str | None = os.environ.get("MILVUS_HOST")
    milvus_port: str | None = os.environ.get("MILVUS_PORT")
    milvus_username: str | None = os.environ.get("MILVUS_USERNAME")
    milvus_collection: str | None = os.environ.get("MILVUS_COLLECTION", "rag_datawhiz")
    text_to_sql_milvus_collection: str | None = os.environ.get("TEXT_TO_SQL_MILVUS_COLLECTION", "text_to_sql_examples")

    class Config:
        env_prefix = "AI_"

class EmailSettings(BaseSettings):
    """Email service configuration settings."""
    api_endpoint: str | None = os.environ.get('EMAIL_API_ENDPOINT')
    api_endpoint_2: str | None = os.environ.get('EMAIL_API_ENDPOINT_2')

    class Config:
        env_prefix = "EMAIL_"

class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""
    opentelemetry_endpoint: str | None = None

    class Config:
        env_prefix = "MONITORING_"

# class Langfuse(BaseSettings):
#     langfuse_host: str = os.environ.get('LANGFUSE_HOST')
#     langfuse_public_key: str = os.environ.get('LANGFUSE_PUBLIC_KEY')
#     langfuse_secret_key: str = os.environ.get("LANGFUSE_SECRET_KEY")
#     langfuse_enabled: str = os.environ.get("LANGFUSE_ENABLED")

class GoogleFirestoreSettings(BaseSettings):
    type: str | None = os.environ.get("GOOGLE_FIRESTORE_TYPE")
    project_id: str | None = os.environ.get("GOOGLE_FIRESTORE_PROJECT_ID")
    private_key_id: str | None = os.environ.get("GOOGLE_FIRESTORE_PRIVATE_KEY_ID")
    private_key: str | None = os.environ.get("GOOGLE_FIRESTORE_PRIVATE_KEY")
    client_email: str | None = os.environ.get("GOOGLE_FIRESTORE_CLIENT_EMAIL")
    client_id: str | None = os.environ.get("GOOGLE_FIRESTORE_CLIENT_ID")
    auth_uri: str | None = os.environ.get("GOOGLE_FIRESTORE_AUTH_URI")
    token_uri: str | None = os.environ.get("GOOGLE_FIRESTORE_TOKEN_URI")
    auth_provider_x509_cert_url: str | None = os.environ.get("GOOGLE_FIRESTORE_AUTH_PROVIDER_X509_CERT_URL")
    client_x509_cert_url: str | None = os.environ.get("GOOGLE_FIRESTORE_CLIENT_X509_CERT_URL")
    universe_domain: str | None = os.environ.get("GOOGLE_FIRESTORE_UNIVERSE_DOMAIN")
    env_identifier: str | None = os.environ.get("GOOGLE_FIRESTORE_ENV_IDENTIFIER")
    ip_url: str | None = os.environ.get("GOOGLE_FIRESTORE_IP_URL")

    class Config:
        env_prefix = "GOOGLE_FIRESTORE_"

class SmtpSettings(BaseSettings):
    smtp_server: str | None = os.environ.get("SMTP_SERVER")
    smtp_email: str | None = os.environ.get("SMTP_EMAIL")
    smtp_password: str | None = os.environ.get("SMTP_PASSWORD")
    smtp_port: int | None = int(os.environ.get("SMTP_PORT", "587")) if os.environ.get("SMTP_PORT") else None
    smtp_email_to: str | None = os.environ.get("SMTP_EMAIL_TO")
    smtp_email_cc: str | None = os.environ.get("SMTP_EMAIL_CC")
    class Config:
        env_prefix = "SMTP_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    redis_host: str = os.environ.get("REDIS_HOST", "localhost")
    redis_port: int = int(os.environ.get("REDIS_PORT", "6379"))
    redis_password: str | None = os.environ.get("REDIS_PASSWORD")
    redis_db: int = int(os.environ.get("REDIS_DB", "0"))
   
    class Config:
        env_prefix = "REDIS_"


class Settings(BaseSettings):
    """Application settings."""
    app: ApplicationSettings = ApplicationSettings()
    db: DatabaseSettings = DatabaseSettings()
    # azure: AzureSettings = AzureSettings()
    # gcp: GCPSettings = GCPSettings()
    # databricks: DatabricksSettings = DatabricksSettings()
    # ai: AISettings = AISettings()
    email: EmailSettings = EmailSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    # langfuse: Langfuse = Langfuse()
    # google_firestore: GoogleFirestoreSettings = GoogleFirestoreSettings()
    smtp_settings:  SmtpSettings = SmtpSettings()
    redis: RedisSettings = RedisSettings()

    @property
    def redis_password(self) -> str:
        return self.azure.redis_password
    # Backward compatibility properties
    @property
    def host(self) -> str:
        return self.app.host
    
    @property
    def port(self) -> int:
        return self.app.port
    
    @property
    def workers_count(self) -> int:
        return self.app.workers_count
    
    @property
    def reload(self) -> bool:
        return self.app.reload
    
    @property
    def environment(self) -> str:
        return self.app.environment
    
    @property
    def log_level(self) -> LogLevel:
        return self.app.log_level
    
    @property
    def app_title(self) -> str:
        return self.app.app_title
    
    @property
    def app_version(self) -> str:
        return self.app.app_version
    
    @property
    def logging_environment(self) -> str:
        return self.app.logging_environment
    
    @property
    def project_id(self) -> str | None:
        return self.app.project_id
    
    # Database backward compatibility
    @property
    def db_url(self) -> URL:
        return self.db.url
    
    
    @property
    def db_host(self) -> str | None:
        return self.db.POSTGRES_DB_HOST
    
    @property
    def db_port(self) -> str | None:
        return self.db.POSTGRES_DB_PORT
    
    @property
    def db_user(self) -> str | None:
        return self.db.POSTGRES_DB_USERNAME
    
    @property
    def db_pass(self) -> str | None:
        return self.db.POSTGRES_DB_PASSWORD

    @property
    def db_name(self) -> str | None:
        return self.db.POSTGRES_DB_NAME
    
    @property
    def db_schema_name(self) -> str | None:
        return self.db.POSTGRES_SCHEMA_NAME
    
    @property
    def db_echo(self) -> bool:
        return False
    
    # Azure backward compatibility
    @property
    def azure_api_key(self) -> str | None:
        return self.azure.api_key
    
    @property
    def azure_api_version(self) -> str | None:
        return self.azure.api_version
    
    @property
    def azure_endpoint(self) -> str | None:
        return self.azure.endpoint
    
    @property
    def azure_deployment(self) -> str | None:
        return self.azure.deployment
    
    @property
    def modelAzure(self) -> str | None:
        return self.azure.model_4o  # Using model_4o as the default Azure model
    
    @property
    def model(self) -> str | None:
        return self.ai.llm_model_name  # Using llm_model_name as the default model
    
    @property
    def embeddings_model(self) -> str | None:
        return os.environ.get('AZURE_EMBEDDINGS_MODEL')  # Direct access to EMBEDDINGS_model
    
    @property
    def azure_deployment_4o(self) -> str | None:
        return self.azure.deployment_4o
    
    @property
    def azure_deployment_model_4o(self) -> str | None:
        return self.azure.model_4o
    
    @property
    def azure_deployment_4o_version(self) -> str | None:
        return self.azure.development_version  # Using the same API version for 4o
    
    @property
    def azure_embedding_deployment(self) -> str | None:
        return self.azure.embedding_deployment
    
    @property
    def deploymentAzure(self) -> str | None:
        return self.azure.deployment_4o
    
    @property
    def gcp_service_account_json(self) -> str | None:
        # Create JSON string from GCP service account components
        import json
        import logging
        
        logger = logging.getLogger(__name__)        
        service_account_info = {
            "type": self.gcp.google_type,
            "project_id": self.gcp.google_project_id,
            "private_key_id": self.gcp.google_private_key_id,
            "private_key": self.gcp.google_private_key,
            "client_email": self.gcp.google_client_email,
            "client_id": self.gcp.google_client_id,
            "auth_uri": self.gcp.google_auth_uri,
            "token_uri": self.gcp.google_token_uri,
            "auth_provider_x509_cert_url": self.gcp.google_auth_provider_x509_cert_url,
            "client_x509_cert_url": self.gcp.google_client_x509_cert_url,
            "universe_domain": self.gcp.google_universe_domain
        }
        
        # Fix the private key by replacing literal \n with actual newlines
        if service_account_info.get("private_key"):
            service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
        
        # Only return JSON if we have the essential fields including private_key
        if (service_account_info.get("type") and 
            service_account_info.get("project_id") and 
            service_account_info.get("private_key") and
            service_account_info.get("client_email")):
            logger.info("All required GCP service account fields are present")
            return json.dumps(service_account_info)
        else:
            logger.error("Missing required GCP service account fields:")
            logger.error(f"type: {service_account_info.get('type')}")
            logger.error(f"project_id: {service_account_info.get('project_id')}")
            logger.error(f"private_key: {'SET' if service_account_info.get('private_key') else 'NOT SET'}")
            logger.error(f"client_email: {service_account_info.get('client_email')}")
        return None
    
    @property
    def goole_firestore_service_account_dict(self) -> str | None:
        # Create JSON string from GCP service account components
        import json
        import logging
        
        logger = logging.getLogger(__name__)        
        google_firestore_service_account: dict = {
            "type": self.google_firestore.type,
            "project_id": self.google_firestore.project_id,
            "private_key_id": self.google_firestore.private_key_id,
            "private_key": self.google_firestore.private_key,
            "client_email": self.google_firestore.client_email,
            "client_id": self.google_firestore.client_id,
            "auth_uri": self.google_firestore.auth_uri,
            "token_uri": self.google_firestore.token_uri,
            "auth_provider_x509_cert_url": self.google_firestore.auth_provider_x509_cert_url,
            "client_x509_cert_url": self.google_firestore.client_x509_cert_url,
            "universe_domain": self.google_firestore.universe_domain,
            "env_identifier":self.google_firestore.env_identifier,
            "ip_url": self.google_firestore.ip_url
        }
        
        # Fix the private key by replacing literal \n with actual newlines
        if google_firestore_service_account.get("private_key"):
            google_firestore_service_account["private_key"] = google_firestore_service_account["private_key"].replace("\\n", "\n")
        
        # Only return JSON if we have the essential fields including private_key
        if (google_firestore_service_account.get("type") and 
            google_firestore_service_account.get("project_id") and 
            google_firestore_service_account.get("private_key") and
            google_firestore_service_account.get("client_email")):
            logger.info("All required google_firestore service account fields are present")
            return google_firestore_service_account
        else:
            logger.error("Missing required google_firestore service account fields:")
            logger.error(f"type: {google_firestore_service_account.get('type')}")
            logger.error(f"project_id: {google_firestore_service_account.get('project_id')}")
            logger.error(f"private_key: {'SET' if google_firestore_service_account.get('private_key') else 'NOT SET'}")
            logger.error(f"client_email: {google_firestore_service_account.get('client_email')}")
        return None
    
    @property
    def tenant_id(self) -> str | None:
        return self.azure.tenant_id
    
    @property
    def client_id(self) -> str | None:
        return self.azure.client_id
    
    @property
    def client_secret(self) -> str | None:
        return self.azure.client_secret
    
    @property
    def service_bus_namespace(self) -> str | None:
        return self.azure.service_bus_namespace
    
    @property
    def SERVICE_BUS_KEY(self) -> str | None:
        return self.azure.service_bus_key
    
    # GCP backward compatibility
    @property
    def gcp_project_id(self) -> str | None:
        return self.gcp.google_project_id
    @property
    def project_id_video(self) -> str | None:
        return self.gcp.project_id_video
    @property
    def topic_id_video(self) -> str | None:
        return self.gcp.topic_id_video
    @property
    def video_scripts_to_create(self) -> str | None:
        return self.gcp.video_scripts_to_create
    
    
    @property
    def region(self) -> str | None:
        return self.gcp.region
    
    @property
    def gcs_bucket_name(self) -> str | None:
        return self.gcp.bucket_name
    
    @property
    def vertexai_region(self) -> str | None:
        return self.gcp.vertexai_region
    @property
    def model_api_endpoint(self)->str | None:
        return self.gcp.model_api_endpoint
    
    @property
    def index_id(self) -> str | None:
        return self.gcp.index_id
    
    @property
    def endpoint_id(self) -> str | None:
        return self.gcp.endpoint_id
    
    @property
    def model_name(self) -> str | None:
        return self.ai.model_name
    
    # GCP Model backward compatibility
    @property
    def GCP_MODEL_326(self) -> str | None:
        return self.gcp.model_326
    
    @property
    def GCP_MODEL_331(self) -> str | None:
        return self.gcp.model_331
    
    @property
    def GCP_MODEL_391(self) -> str | None:
        return self.gcp.model_391
    
    @property
    def GCP_EXPLAINER_326(self) -> str | None:
        return self.gcp.explainer_326
    
    @property
    def GCP_EXPLAINER_331(self) -> str | None:
        return self.gcp.explainer_331
    
    @property
    def GCP_EXPLAINER_391(self) -> str | None:
        return self.gcp.explainer_391
    
    # New config for GuestPulse
    @property
    def guestpulse_labelencode_endpoint_id(self) -> str | None:
        return self.gcp.guestpulse_labelencode_endpoint_id
   
    @property
    def guestpulse_xgboost_endpoint_id(self) -> str | None:
        return self.gcp.guestpulse_xgboost_endpoint_id
   
    @property
    def guestpulse_prophet_endpoint_id(self) -> str | None:
        return self.gcp.guestpulse_prophet_endpoint_id
    
    @property
    def guestpulse_req_url(self) -> str | None:
        return self.gcp.guestpulse_req_url
    
    # Databricks backward compatibility
    @property
    def DATABRICKS_HOST(self) -> str | None:
        return self.databricks.data_bricks_host
    
    @property
    def DATABRICKS_TOKEN(self) -> str | None:
        return self.databricks.data_bricks_token
    
    @property
    def databricks_endpoint_name(self) -> str | None:
        return self.databricks.data_bricks_endpoint_name
    
    @property
    def databricks_endpoint_dynamic_name(self) -> str | None:
        return self.databricks.data_bricks_endpoint_dynamic_name
    
    @property
    def base_schema(self) -> str | None:
        return self.databricks.base_schema
    
    @property
    def databricks_endpoint_gcp_name(self) -> str | None:
        return self.databricks.data_bricks_endpoint_gcp_name
    
    @property
    def base_gcp_schema(self) -> str | None:
        return self.databricks.base_gcp_schema
    
    @property
    def DATABRICKS_MODEL_326(self) -> str | None:
        return self.databricks.data_bricks_model_326
    
    @property
    def DATABRICKS_MODEL_331(self) -> str | None:
        return self.databricks.data_bricks_model_331
    
    @property
    def DATABRICKS_MODEL_391(self) -> str | None:
        return self.databricks.data_bricks_model_391
    
    @property
    def DATABRICKS_EXPLAINER_326(self) -> str | None:
        return self.databricks.data_bricks_explainer_326
    
    @property
    def DATABRICKS_EXPLAINER_331(self) -> str | None:
        return self.databricks.data_bricks_explainer_331
    
    @property
    def DATABRICKS_EXPLAINER_391(self) -> str | None:
        return self.databricks.data_bricks_explainer_391
    
    @property
    def openai_api_type(self) -> str | None:
        return "azure"  # Default for Azure OpenAI
    
    @property
    def openai_api_version(self) -> str | None:
        return self.azure.api_version
    
    @property
    def deployment(self) -> str | None:
        return self.azure.deployment
    
    @property
    def openai_embeddings_deployment(self) -> str | None:
        return self.azure.openai_embeddings_deployment
    
    # AI backward compatibility
    @property
    def llm_model_name(self) -> str | None:
        return self.ai.llm_model_name
    
    @property
    def image_model_name(self) -> str | None:
        return self.ai.image_model_name
    
    @property
    def llm_image_model_name(self) -> str | None:
        return self.ai.llm_image_model_name
    
    @property
    def total_images(self) -> int:
        return self.ai.total_images
    
    @property
    def milvus_host(self) -> str | None:
        return self.ai.milvus_host
    
    @property
    def milvus_port(self) -> str | None:
        return self.ai.milvus_port
    
    @property
    def milvus_username(self) -> str | None:
        return self.ai.milvus_username
    
    @property
    def MILVUS_COLLECTION(self) -> str | None:
        return self.ai.milvus_collection
    
    @property
    def TEXT_TO_SQL_MILVUS_COLLECTION(self) -> str | None:
        return self.ai.text_to_sql_milvus_collection
    
    # Email backward compatibility
    @property
    def email_api_endpoint(self) -> str | None:
        return self.email.api_endpoint
    
    @property
    def email_api_endpoint_2(self) -> str | None:
        return self.email.api_endpoint_2
    
    # Monitoring backward compatibility
    @property
    def opentelemetry_endpoint(self) -> str | None:
        return self.monitoring.opentelemetry_endpoint

    @property
    def POSTGRES_SCHEMA_CONFIG(self) -> str | None:
        return self.db.POSTGRES_SCHEMA_CONFIG

    @property
    def smtp_server(self) -> str | None:
        return self.smtp_settings.smtp_server
    
    @property
    def smtp_port(self) -> int | None:
        return self.smtp_settings.smtp_port
    
    @property
    def smtp_email(self) -> str | None:
        return self.smtp_settings.smtp_email
    
    @property
    def smtp_password(self) -> str | None:
        return self.smtp_settings.smtp_password

    @property
    def smtp_email_to(self) -> str | None:
        return self.smtp_settings.smtp_email_to

    @property
    def smtp_email_cc(self) -> str | None:
        return self.smtp_settings.smtp_email_cc
    
    # Redis backward compatibility
    @property
    def redis_host(self) -> str:
        return self.redis.redis_host
    
    @property
    def redis_port(self) -> int:
        return self.redis.redis_port
    
    @property
    def redis_password(self) -> str | None:
        return self.redis.redis_password
    
    @property
    def redis_db(self) -> int:
        return self.redis.redis_db
    
    # JWT backward compatibility
    @property
    def jwt_secret(self) -> str:
        return self.app.jwt_secret
    
    @property
    def jwt_algorithm(self) -> str:
        return self.app.jwt_algorithm
    
    @property
    def access_token_expire_minutes(self) -> int:
        return self.app.access_token_expire_minutes
    
    @property
    def refresh_token_expire_days(self) -> int:
        return self.app.refresh_token_expire_days

    
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()