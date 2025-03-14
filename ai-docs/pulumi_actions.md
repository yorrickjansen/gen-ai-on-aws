# Pulumi GitHub Actions

Pulumi's GitHub Actions deploy apps and infrastructure to your cloud of choice, using just your favorite language and GitHub. This includes previewing, validating, and collaborating on proposed deployments in the context of Pull Requests, and triggering deployments or promotions between different environments by merging or directly committing code.

## Getting Started

```yaml
name: Pulumi
on:
  push:
    branches:
      - main
jobs:
  up:
    name: Preview
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pulumi/actions@v6
        with:
          command: preview
          stack-name: org-name/stack-name
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
```

This will check out the existing directory and run `pulumi preview`.

## Configuration

The action can be configured with the following arguments:

- `command` (optional) - The command to run as part of the action. Accepted values are `up` (alias: update), `refresh`, `destroy`, `preview` and `output`. If unspecified, the action will stop after installing Pulumi.

- `stack-name` (optional) - The name of the stack that Pulumi will be operating on. Use the fully quaified org-name/stack-name when operating on a stack outside of your individual account. This field is required if a `command` was specified.

- `work-dir` (optional) - The location of your Pulumi files. Defaults to `./`.

- `cloud-url` (optional) - the Pulumi backend to login to. This would be the equivalent of what would be passed to the `pulumi login` command.

- `comment-on-pr` (optional) If `true`, then the action will add the results of the Pulumi action to the PR. Ignored unless `${{ github.event }}` type is `pull_request`.

- `comment-on-summary` (optional) If `true`, then the action will add the results of the Pulumi action to the GitHub step summary.

- `github-token` (optional) A GitHub token that has access levels to allow the Action to comment on a PR. Defaults to `${{ github.token }}`

- `refresh` (optional) If `true`, `preview` and `up` commands are called with the `--refresh` flag.

- `secrets-provider` (optional) The type of the provider that should be used to encrypt and decrypt secrets. Possible choices: `default`, `passphrase`, `awskms`, `azurekeyvault`, `gcpkms`, `hashivault`.

- `color` (optional) Colorize output. Choices are: always, never, raw, auto (default "auto").

### Extra options

- `config-map` (optional) Configuration of the stack. Format Yaml string: `{<key | string>: {value: <value | string>, secret: <is_secret | boolean> },}`.

- `diff` (optional) Display operation as a rich diff showing the overall change.

- `comment-on-pr-number` (optional) If set to a number, then the action will add the results of the Pulumi action to the specified PR number.

- `edit-pr-comment` (optional) Edit previous PR comment instead of posting new one. **NOTE:** as of 3.2.0 of the Action, this now defaults to `true`.

- `expect-no-changes` (optional) Return an error if any changes occur during this update.

- `message` (optional) Optional message to associate with the update operation.

- `parallel` (optional) Allow P resource operations to run in parallel at once (1 for no parallelism). Defaults to unbounded.

- `policyPacks` (optional) Run one or more policy packs with the provided `command`.

- `policyPackConfigs` (optional) Path(s) to JSON file(s) containing the config for the policy pack.

- `pulumi-version` (optional) Install a specific version of the Pulumi CLI. Defaults to "^3".

- `pulumi-version-file` (optional) File containing the version of the Pulumi CLI to install.

- `remove` (optional) Removes the target stack if all resources are destroyed. Used only with `destroy` command.

- `replace` (optional) Specify resources to replace.

- `target` (optional) Specify a single resource URN to update. Other resources will not be updated.

- `target-dependents` (optional) Allows updating of dependent targets discovered but not specified in target.

- `upsert` (optional) Allows the creation of the specified stack if it currently doesn't exist.

- `exclude-protected` (optional) Skip destroying protected resources. Only valid when `command` is `destroy`.

- `suppress-outputs` (optional) Suppress display of stack outputs (in case they contain sensitive values).

- `suppress-progress` (optional) Suppress display of periodic progress dots to limit logs length.

- `plan` (optional) Used for [update plans](https://www.pulumi.com/docs/concepts/update-plans/)

- `always-include-summary` (optional) If `true`, then the action will trim long PR comments from the front instead of the back.

- `continue-on-error` (optional) If `true`, then the action will continue running even if an error occurs.

## Stack Outputs

[Stack outputs](https://www.pulumi.com/docs/intro/concepts/stack/#outputs) are available when using this action:

```yaml
- uses: pulumi/actions@v6
  id: pulumi
  env:
    PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}
  with:
    command: up
    cloud-url: gs://my-bucket
    stack-name: org-name/stack-name
- run: echo "My pet name is ${{ steps.pulumi.outputs.pet-name }}"
```

## Example workflows

- [NodeJS Runtime + Pulumi Managed Backend](https://github.com/pulumi/actions/blob/main/examples/nodejs-pulumi.yaml)
- [Python Runtime + Pulumi Managed Backend](https://github.com/pulumi/actions/blob/main/examples/python-pulumi.yaml)
- [Go Runtime + Pulumi Managed Backend](https://github.com/pulumi/actions/blob/main/examples/go-pulumi.yaml)
- [DotNet Runtime + Pulumi Managed Backend](https://github.com/pulumi/actions/blob/main/examples/dotnet-pulumi.yaml)
- [NodeJS Runtime + AWS S3 Self Managed Backend](https://github.com/pulumi/actions/blob/main/examples/nodejs-aws.yaml)
- [NodeJS Runtime + Google GCS Self Managed Backend](https://github.com/pulumi/actions/blob/main/examples/nodejs-google.yaml)
- [NodeJS Runtime + Azure Blob Self Managed Backend](https://github.com/pulumi/actions/blob/main/examples/nodejs-azure.yaml)
- [NodeJS Runtime + Local File System Self Managed Backend](https://github.com/pulumi/actions/blob/main/examples/nodejs-local.yaml)