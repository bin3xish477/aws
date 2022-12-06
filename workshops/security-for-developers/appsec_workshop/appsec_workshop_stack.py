from constructs import Construct
import aws_cdk as cdk

from .infra import Infra
from .devtools import DevTools
from .tasks import Tasks
from .pipeline import Pipeline


class AppsecWorkshopStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### CDK Constructs for the Base Infra
        infra = Infra(self, "Infra")

        ### CDK Constructs for the Developer Tools
        devtools = DevTools(self, "DevTools", infra, config)

        ### CDK Constructs for the ECS Fargate Tasks
        tasks = Tasks(self, "Tasks", infra, devtools, config)

        ### CDK Constructs for the DevSecOps Pipeline
        pipeline = Pipeline(self, "Pipeline", devtools, tasks, config)
        
