"""Provisioning resources for GitHub Actions OIDC integration."""

import json
from typing import List

import pulumi
import pulumi_aws as aws


def create_github_actions_oidc_provider(
    github_repo: str, allowed_branches: List[str] = ["main", "releases/demo"]
) -> aws.iam.OpenIdConnectProvider:
    """Create an OIDC provider for GitHub Actions.

    Args:
        github_repo: The GitHub repository (in format: org/repo)
        allowed_branches: List of branches allowed to authenticate

    Returns:
        The OIDC provider resource
    """
    # Create the OIDC provider for GitHub Actions
    github_actions_provider = aws.iam.OpenIdConnectProvider(
        "github-actions-oidc-provider",
        client_id_lists=["sts.amazonaws.com"],
        thumbprint_lists=["6938fd4d98bab03faadb97b34396831e3780aea1"],
        url="https://token.actions.githubusercontent.com",
    )

    # Create a condition to verify the repository and branch
    condition_json = json.dumps(
        {
            "StringLike": {
                "token.actions.githubusercontent.com:sub": [
                    f"repo:{github_repo}:ref:refs/heads/{branch}"
                    for branch in allowed_branches
                ]
            }
        }
    )

    # Create a role that can be assumed by GitHub Actions
    github_actions_role = aws.iam.Role(
        "github-actions-role",
        assume_role_policy=pulumi.Output.all(github_actions_provider.arn).apply(
            lambda args: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Federated": args[0],
                            },
                            "Action": "sts:AssumeRoleWithWebIdentity",
                            "Condition": json.loads(condition_json),
                        }
                    ],
                }
            )
        ),
        description="Role used by GitHub Actions for deployments",
        tags={
            "Name": "github-actions-role",
            "Purpose": "GitHub Actions OIDC integration",
        },
    )

    # Attach policies to the role
    aws.iam.RolePolicyAttachment(
        "github-actions-aws-policy",
        role=github_actions_role.name,
        policy_arn="arn:aws:iam::aws:policy/AdministratorAccess",  # Use more restrictive policy in production!
    )

    # Export the role ARN so it can be used in GitHub secrets
    pulumi.export("github_actions_role_arn", github_actions_role.arn)

    return github_actions_provider
