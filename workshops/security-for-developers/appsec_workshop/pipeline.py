from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns
)

class Pipeline(Construct):

    def __init__(self, scope: Construct, id: str, devtools, tasks, config: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        ### CodePipeline
        pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name="devsecops-pipeline",
            stages=[]
        )

        ### Source Stage
        source_output = codepipeline.Artifact()
        pipeline.add_stage(
            stage_name="CheckoutSource",
            actions=[
                codepipeline_actions.CodeCommitSourceAction(
                    action_name="CodeCommit",
                    repository=devtools.code_repo,
                    output=source_output,
                    run_order=1
                )
            ]
        )

        ### Static Application Security Analysis (SAST) Stage
        security_ci = pipeline.add_stage(
            stage_name="ApplicationSecurityChecks"
        )
        if config['sast']['enabled']:
            sast = codebuild.PipelineProject(
                self, "SAST",
                project_name="codebuild-sast-project",
                build_spec=codebuild.BuildSpec.from_source_filename(
                    filename="sast_buildspec.yaml"
                ),
                environment=codebuild.BuildEnvironment(
                    privileged=True,
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3
                ),
                environment_variables={
                    "SONARQUBE_URL": codebuild.BuildEnvironmentVariable(
                        value="http://{}".format(devtools.sonarqube.load_balancer.load_balancer_dns_name)
                    ),
                    "SONARQUBE_ACCESS_TOKEN": codebuild.BuildEnvironmentVariable(
                        value=config['sast']['sonarqube']['token']
                    )
                },
                description="SAST",
                timeout=cdk.Duration.minutes(60)
            )
            ## Add CodeBuild Project to Pipeline
            security_ci.add_action(
                codepipeline_actions.CodeBuildAction(
                    action_name="SAST",
                    input=source_output,
                    project=sast,
                    run_order=2
                )
            )

        ### Software Component Analysis (SCA) Stage
        if config['sca']['enabled']:
            ## CodeBuild Project
            sca = codebuild.PipelineProject(
                self, "SCA",
                project_name="codebuild-sca-project",
                build_spec=codebuild.BuildSpec.from_source_filename(
                    filename="sca_buildspec.yaml"
                ),
                environment=codebuild.BuildEnvironment(
                    privileged=True,
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3
                ),
                description="Software Component Analysis",
                timeout=cdk.Duration.minutes(60)
            )
            ## Add CodeBuild Project to Pipeline
            security_ci.add_action(
                codepipeline_actions.CodeBuildAction(
                    action_name="SCA",
                    input=source_output,
                    project=sca,
                    run_order=2
                )
            )

        ### License Analysis Stage
        if config['license']['enabled']:
            ## CodeBuild Project
            license = codebuild.PipelineProject(
                self, "LicenseCheck",
                project_name="codebuild-license-check-project",
                build_spec=codebuild.BuildSpec.from_source_filename(
                    filename="license_check_buildspec.yaml"
                ),
                environment=codebuild.BuildEnvironment(
                    privileged=True,
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3
                ),
                description="License Check",
                timeout=cdk.Duration.minutes(60)
            )
            ## Add CodeBuild Project to Pipeline
            security_ci.add_action(
                codepipeline_actions.CodeBuildAction(
                    action_name="Licenses",
                    input=source_output,
                    project=license,
                    run_order=2
                )
            )

        ### Build Docker Image Stage
        build_output = codepipeline.Artifact()
        ## CodeBuild Project
        docker = codebuild.PipelineProject(
            self, "DockerBuild",
            project_name="codebuild-docker-project",
            build_spec=codebuild.BuildSpec.from_source_filename(
                filename="docker_buildspec.yaml"
            ),
            environment=codebuild.BuildEnvironment(
                privileged=True,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3
            ),
            environment_variables={
                "ECR_REPO_URI": codebuild.BuildEnvironmentVariable(
                    value=devtools.ecr_repo.repository_uri
                )
            },
            description="Docker Build Project",
            timeout=cdk.Duration.minutes(60)
        ) 
        # Allow CodeBuild Project rights to ECR repo
        devtools.ecr_repo.grant_pull_push(docker)
        ## Add CodeBuild Project to Pipeline
        pipeline.add_stage(
            stage_name="BuildImage",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="DockerBuildImage",
                    input=source_output,
                    outputs=[build_output],
                    project=docker,
                    run_order=3
                )
            ]
        )

        ### Deploy Staging Environment Stage
        if config['auto_deploy_staging']:
            pipeline.add_stage(
                stage_name="DeployToStaging",
                actions=[
                    codepipeline_actions.EcsDeployAction(
                        action_name="DeployToStaging",
                        input=build_output,
                        service=tasks.flask_app.service,
                        deployment_timeout=cdk.Duration.minutes(60),
                        run_order=4
                    )
                ]
            )

        ### Dynamic Application Security Analysis (DAST) Stage
        report_output = codepipeline.Artifact()
        if config['dast']['enabled'] and config['auto_deploy_staging']:
            dast = codebuild.PipelineProject(
                self, "DAST",
                project_name="codebuild-dast-project",
                build_spec=codebuild.BuildSpec.from_source_filename(
                    filename="dast_buildspec.yaml"
                ),
                environment=codebuild.BuildEnvironment(
                    privileged=True,
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3
                ),
                environment_variables={
                    "ZAP_API_URL": codebuild.BuildEnvironmentVariable(
                        value="http://{}:8080".format(devtools.zaproxy.instance_public_dns_name)
                    ),
                    "ZAP_API_KEY": codebuild.BuildEnvironmentVariable(
                        value=config['dast']['zaproxy']['api_key']
                    ),
                    "SCAN_URL": codebuild.BuildEnvironmentVariable(
                        value="http://{}".format(tasks.flask_app.load_balancer.load_balancer_dns_name)
                    )
                },
                description="DAST",
            )
            ## Add CodeBuild Project to Pipeline
            pipeline.add_stage(
                stage_name="DAST",
                actions=[
                    codepipeline_actions.CodeBuildAction(
                        action_name="DAST",
                        input=source_output,
                        outputs=[report_output],
                        project=dast,
                        run_order=5
                    )
                ]
            )
