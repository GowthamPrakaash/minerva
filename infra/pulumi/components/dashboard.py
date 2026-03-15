import pulumi
import pulumi_aws as aws

class DashboardApp(pulumi.ComponentResource):
    def __init__(self, name: str, env: str, opts: pulumi.ResourceOptions = None):
        super().__init__("minerva:dashboard:DashboardApp", name, {}, opts)

        self.tags = {
            "env": env,
            "component": "dashboard"
        }

        # 1. Amplify App (Minimal for Next.js hosting)
        self.app = aws.amplify.App(
            f"{name}-amplify",
            description="Minerva Dashboard",
            tags=self.tags,
            # Assuming GitHub connection will be added via console or manually
            build_spec='''version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm install
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
''',
            opts=pulumi.ResourceOptions(parent=self)
        )

        # 2. Main Branch (e.g., master or production_ready)
        self.branch = aws.amplify.Branch(
            f"{name}-branch",
            app_id=self.app.id,
            branch_name="master",
            enable_auto_build=True,
            tags=self.tags,
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.app_id = self.app.id
        self.default_domain = self.app.default_domain

        self.register_outputs({
            "app_id": self.app_id,
            "default_domain": self.default_domain
        })
