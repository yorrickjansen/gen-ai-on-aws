# AWS RDS Cluster - Pulumi Python API

This document provides a reference for creating and configuring AWS RDS Aurora clusters using Pulumi with Python.

## Basic Usage

```python
import pulumi
import pulumi_aws as aws

# Create an Aurora MySQL cluster
mysql_cluster = aws.rds.Cluster("mysql-cluster",
    engine=aws.rds.EngineType.AURORA_MYSQL,
    engine_version="5.7.mysql_aurora.2.03.2",
    availability_zones=[
        "us-west-2a",
        "us-west-2b",
        "us-west-2c",
    ],
    database_name="mydb",
    master_username="admin",
    master_password="password123", # Use secrets manager in production
    backup_retention_period=5,
    preferred_backup_window="07:00-09:00",
    skip_final_snapshot=True
)

# Create an Aurora PostgreSQL cluster
postgres_cluster = aws.rds.Cluster("postgres-cluster",
    engine=aws.rds.EngineType.AURORA_POSTGRESQL,
    availability_zones=[
        "us-west-2a",
        "us-west-2b",
        "us-west-2c",
    ],
    database_name="mydb",
    master_username="admin",
    master_password="password123", # Use secrets manager in production
    backup_retention_period=5,
    preferred_backup_window="07:00-09:00",
    skip_final_snapshot=True
)
```

## Serverless v2 Cluster

```python
import pulumi
import pulumi_aws as aws

serverless_cluster = aws.rds.Cluster("serverless-cluster",
    engine=aws.rds.EngineType.AURORA_POSTGRESQL,
    engine_mode=aws.rds.EngineMode.PROVISIONED,
    engine_version="13.6",
    database_name="mydb",
    master_username="admin",
    master_password="password123", # Use secrets manager in production
    storage_encrypted=True,
    serverlessv2_scaling_configuration={
        "max_capacity": 1.0,
        "min_capacity": 0.5,
    },
    skip_final_snapshot=True
)

# Note: You need to also create a cluster instance with the db.serverless class
serverless_instance = aws.rds.ClusterInstance("serverless-instance",
    cluster_identifier=serverless_cluster.id,
    instance_class="db.serverless",
    engine=serverless_cluster.engine,
    engine_version=serverless_cluster.engine_version
)
```

## Using Secrets Manager for Password Management

```python
import pulumi
import pulumi_aws as aws

# Using default KMS key
secrets_manager_cluster = aws.rds.Cluster("secrets-manager-cluster",
    engine=aws.rds.EngineType.AURORA_MYSQL,
    database_name="mydb",
    master_username="admin",
    manage_master_user_password=True,  # Let RDS manage the password in Secrets Manager
    skip_final_snapshot=True
)

# Using a specific KMS key
kms_key = aws.kms.Key("db-password-key", 
    description="KMS key for RDS master password")

secrets_manager_cluster_kms = aws.rds.Cluster("secrets-manager-cluster-kms",
    engine=aws.rds.EngineType.AURORA_MYSQL,
    database_name="mydb",
    master_username="admin",
    manage_master_user_password=True,
    master_user_secret_kms_key_id=kms_key.key_id,
    skip_final_snapshot=True
)
```

## Important Properties

### Required Properties
- `engine`: Database engine (`aurora`, `aurora-mysql`, `aurora-postgresql`, `mysql`, `postgres`)
- `master_username`: Username for the master user

### Common Properties
- `cluster_identifier`: Identifier for the cluster (auto-generated if not specified)
- `database_name`: Name for the initial database
- `master_password`: Password for the master user (not needed with `manage_master_user_password=True`)
- `manage_master_user_password`: Use Secrets Manager to manage the master password
- `availability_zones`: List of AZs where cluster instances can be created (max 3)
- `backup_retention_period`: Days to retain backups (default: 1)
- `preferred_backup_window`: Time range for backups (format: "hh24:mi-hh24:mi")
- `skip_final_snapshot`: Whether to skip the final snapshot when deleting (default: False)
- `final_snapshot_identifier`: Name of the final snapshot (required if `skip_final_snapshot=False`)
- `storage_encrypted`: Whether storage should be encrypted (default: False for provisioned, True for serverless)
- `kms_key_id`: KMS key for encryption (required when `storage_encrypted=True`)

### Serverless v2 Configuration
- `engine_mode`: Set to `aws.rds.EngineMode.PROVISIONED` 
- `serverlessv2_scaling_configuration`: Configuration for capacity scaling
  - `min_capacity`: Minimum ACU capacity (0.5 to 256 in 0.5 increments)
  - `max_capacity`: Maximum ACU capacity (0.5 to 256 in 0.5 increments)

### Enum Values

#### EngineType
- `AURORA`: "aurora"
- `AURORA_MYSQL`: "aurora-mysql"
- `AURORA_POSTGRESQL`: "aurora-postgresql"

#### EngineMode
- `PROVISIONED`: "provisioned"
- `SERVERLESS`: "serverless"
- `PARALLEL_QUERY`: "parallelquery"
- `GLOBAL`: "global"

## Output Properties

- `arn`: The Amazon Resource Name (ARN) of the cluster
- `cluster_resource_id`: The RDS Cluster Resource ID
- `endpoint`: The writer endpoint for the cluster
- `reader_endpoint`: The reader endpoint for load-balanced read-only connections
- `engine_version_actual`: The running version of the database engine
- `hosted_zone_id`: The Route53 Hosted Zone ID of the endpoint
- `master_user_secrets`: Block with master user secret information when using Secrets Manager

## Import

```
pulumi import aws:rds/cluster:Cluster aurora_cluster aurora-prod-cluster
```