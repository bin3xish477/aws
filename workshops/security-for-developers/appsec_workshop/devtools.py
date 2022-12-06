from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam
)

class DevTools(Construct):

    @property
    def code_repo(self):
        return self._code_repo

    @property
    def ecr_repo(self):
        return self._ecr_repo

    @property
    def sonarqube(self):
        return self._sonarqube

    @property
    def zaproxy(self):
        return self._zaproxy

    def __init__(self, scope: Construct, id: str, infra, config: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        ### CodeCommit - code repo
        self._code_repo = codecommit.Repository(
            self, "Repository",
            repository_name="flask-app",
            description="CodeCommit repo for the workshop")

        ### No longer needed if using Cloud9
        # # IAM User for CodeCommit
        # self._iam_user = iam.User(
        #     self, "CodeCommitUser",
        #     user_name="developer"
        # )
        # self._iam_user.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeCommitPowerUser")
        # )

        ### ECR - docker repo
        self._ecr_repo = ecr.Repository(
            self, "ECR",
            repository_name="flask-app",
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # SonarQube Server
        self._sonarqube = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "SonarQube",
            cluster=infra.staging_cluster,
            cpu=1024,
            memory_limit_mib=4096,
            desired_count=1,
            public_load_balancer=True,
            task_image_options={
                "image": ecs.ContainerImage.from_registry(config['sast']['sonarqube']['image']),
                "container_port": 9000,
                "enable_logging": True
            }
        )

        # OWASP Zap Server
        ami = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
            cpu_type=ec2.AmazonLinuxCpuType.X86_64
        )

        security_group = ec2.SecurityGroup(
            self, "OWASPZapSG",
            vpc=infra.staging_vpc,
        )

        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(8080),
        )

        with open("./user_data/zaproxy_bootstrap.sh") as f:
            user_data = f.read()

        user_data = user_data.replace("$API_KEY", config['dast']['zaproxy']['api_key'])
        
        self._zaproxy = ec2.Instance(
            self, "Zaproxy",
            instance_type=ec2.InstanceType(config['dast']['zaproxy']['instance_type']),
            vpc=infra.staging_vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=security_group,
            machine_image=ami,
            user_data=ec2.UserData.custom(user_data)
        )
