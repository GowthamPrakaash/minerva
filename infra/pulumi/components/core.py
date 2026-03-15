import pulumi
import pulumi_aws as aws

class CoreService(pulumi.ComponentResource):
    def __init__(self, name: str, env: str, base_infra, opts: pulumi.ResourceOptions = None):
        super().__init__("minerva:core:CoreService", name, {}, opts)

        self.tags = {
            "env": env,
            "component": "core"
        }

        # 1. ECR Repository for Core
        self.repo = aws.ecr.Repository(
            f"{name}-repo",
            force_delete=True,
            tags=self.tags,
            opts=pulumi.ResourceOptions(parent=self)
        )

        # 2. Log Group
        self.log_group = aws.cloudwatch.LogGroup(
            f"/ecs/{name}-core",
            retention_in_days=3,
            tags=self.tags,
            opts=pulumi.ResourceOptions(parent=self)
        )

        # 3. Load Balancer (ALB) for Core API
        self.alb_sg = aws.ec2.SecurityGroup(
            f"{name}-alb-sg",
            vpc_id=base_infra.vpc.vpc_id,
            ingress=[{"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]}],
            egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}],
            tags=self.tags,
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.alb = aws.lb.LoadBalancer(
            f"{name}-alb",
            security_groups=[self.alb_sg.id],
            subnets=base_infra.vpc.public_subnet_ids,
            tags=self.tags,
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.target_group = aws.lb.TargetGroup(
            f"{name}-tg",
            port=8000,
            protocol="HTTP",
            vpc_id=base_infra.vpc.vpc_id,
            target_type="ip",
            health_check={"path": "/health"},
            tags=self.tags,
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.listener = aws.lb.Listener(
            f"{name}-listener",
            load_balancer_arn=self.alb.arn,
            port=80,
            default_actions=[{
                "type": "forward",
                "target_group_arn": self.target_group.arn
            }],
            tags=self.tags,
            opts=pulumi.ResourceOptions(parent=self)
        )

        # 4. ECS Service (1 vCPU, 1 GB RAM, as requested)
        self.task_def = aws.ecs.TaskDefinition(
            f"{name}-core-task",
            family=f"{name}-core",
            requires_compatibilities=["FARGATE"],
            network_mode="awsvpc",
            cpu="1024",
            memory="1024",
            execution_role_arn=base_infra.ecs_execution_role.arn,
            tags=self.tags,
            container_definitions=pulumi.Output.format('''[
                {{
                    "name": "core",
                    "image": "{0}",
                    "portMappings": [{{"containerPort": 8000, "hostPort": 8000}}],
                    "environment": [
                        {{"name": "DATABASE_URL", "value": "{1}"}},
                        {{"name": "ENV", "value": "production"}}
                    ],
                    "logConfiguration": {{
                         "logDriver": "awslogs",
                         "options": {{
                            "awslogs-group": "{2}",
                            "awslogs-region": "{3}",
                            "awslogs-stream-prefix": "ecs"
                         }}
                    }}
                }}
            ]''', self.repo.repository_url, base_infra.db_url, self.log_group.name, aws.get_region().region),
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.service = aws.ecs.Service(
            f"{name}-service",
            cluster=base_infra.cluster.arn,
            task_definition=self.task_def.arn,
            desired_count=1,
            launch_type="FARGATE",
            network_configuration={
                "subnets": base_infra.vpc.private_subnet_ids,
                "security_groups": [base_infra.db_sg.id] # Reuse SG for internal traffic
            },
            tags=self.tags,
            load_balancers=[{
                "target_group_arn": self.target_group.arn,
                "container_name": "core",
                "container_port": 8000
            }],
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.service_url = pulumi.Output.format(
            "http://{0}",
            self.alb.dns_name
        )
        self.register_outputs({
            "service_url": self.service_url
        })
