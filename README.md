# AWS CloudFormation Role

This is an Ansible role for generating CloudFormation templates and deploying CloudFormation stacks to Amazon Web Services.

## Requirements

- Python 2.7
- PIP package manager (**easy_install pip**)
- Ansible 2.2 or greater (**pip install ansible**)
- Boto (**pip install boto**)
- Boto3 (**pip install boto3**)
- Netaddr (**pip install netaddr**)
- AWS CLI (**pip install awscli**) installed and configured
- [jq](https://stedolan.github.io/jq/)

## Setup

The recommended approach to use this role is an Ansible Galaxy requirement to your Ansible playbook project.

Alternatively you can also configure this repository as a Git submodule to your Ansible playbook project.

The role should be placed in the folder **roles/aws-cloudformation**, and can then be referenced from your playbooks as a role called `aws-cloudformation`.

You should also specify a specific release that is compatible with your playbook.

### Install using Ansible Galaxy

To set this role up as an Ansible Galaxy requirement, first create a `requirements.yml` file in a `roles` subfolder of your playbook and add an entry for this role.  See the [Ansible Galaxy documentation](http://docs.ansible.com/ansible/galaxy.html#installing-multiple-roles-from-a-file) for more details.

```
# Example requirements.yml file
- src: git@github.com:Casecommons/aws-cloudformation.git
  scm: git
  version: 0.1.0
  name: aws-cloudformation
```

Once you have created `requirements.yml`, you can install the role using the `ansible-galaxy` command line tool.

```
$ ansible-galaxy install -r roles/requirements.yml -p ./roles/ --force
```

To update the role version, simply update the `requirements.yml` file and re-install the role as demonstrated above.

### Installing using Git Submodule

You can also install this role by adding this repository as a Git submodule and then checking out the required version:

```
$ git submodule add git@github.com:Casecommons/aws-cloudformation.git roles/aws-cloudformation
Submodule path 'roles/aws-cloudformation': checked out '05f584e53b0084f1a2a6a24de6380233768a1cf0'
$ cd roles/aws-cloudformation
roles/aws-cloudformation$ git checkout 0.1.0
roles/aws-cloudformation$ cd ../..
$ git commit -a -m "Added aws-cloudformation 0.1.0 role"
```

If you add this role as a submodule, you can update to later versions of this role by updating your submodules:

```
$ git submodule update --remote roles/aws-cloudformation
$ cd roles/aws-cloudformation
roles/aws-cloudformation$ git checkout 0.2.0
roles/aws-cloudformation$ cd ../..
$ git commit -a -m "Updated to aws-cloudformation 0.2.0 role"
```

## Usage

This role is designed to be used with CloudFormation stacks and relies on a CloudFormation template file being provided by the consuming playbook.

The default convention is to create the template file at the path `templates/stack.yml.j2` in the playbook repository.

> You can override the default template file by setting the `cf_stack_template` variable.

The expected format of the CloudFormation template is a [Jinja2 template](http://jinja.pocoo.org/docs/dev/), although you can provide a literal template.  This allows you to perform Jinja2 template variable substitution and more advanced constructs to generate your CloudFormation templates.

The recommended approach is to describe your template in a YAML format, as this role will automatically convert to a minified JSON format.

> This role does not currently support AWS YAML syntax.  The role will convert your template and upload the template as JSON.

The following variables are used to configure this role:

- `cf_stack_name` (required) - defines the stack name
- `cf_stack_inputs` (optional) - a dictionary of stack inputs to provide to the stack.  These will be autogenerated according to conventions defined in the [Stack Inputs](#stack-inputs) section, however you can explicitly define your stack inputs if you wish using this variable.
- `cf_stack_policy` (optional) - defines the stack policy in a YAML or JSON format.
- `cf_s3_bucket` (optional) - defines the S3 bucket where the CloudFormation template will be uploaded.  This defaults to `<account-id>-cfn-templates` if not specified.
- `cf_s3_upload` (optional) - uploads the generated CloudFormation template to an S3 bucket defined by the `cf_s3_bucket` variable.  Defaults to `false`.

Invoking this role will generate a folder called `build` in the current working directory, along with a timestamped folder of the current date (e.g. `./build/20160705154440/`).  Inside this folder the following files are created:

- `stack.yml` - the generated CloudFormation template in human readable YAML format.
- `stack.json` - the generated CloudFormation template in compact JSON format.  This is the template that is uploaded to the AWS CloudFormation service when creating or updating a stack.
- `policy.json` - the stack policy JSON file that is uploaded to the AWS CloudFormation service.


### Stack Inputs

The template generator supports auto generating stack inputs based upon the following conventions:

- Each stack template parameter is defined in a variable named `config_<snake-case-version-of-stack-parameter>`.  E.g. if the template parameter is `ApplicationInstanceType` - you need to have `config_application_instance_type` defined in your environment settings.
- If `config_<snake-case-version-of-stack-parameter>` is not defined but the parameter has a `Default` property, then the `Default` property value will be used
- If `config_<snake-case-version-of-stack-parameter>` is not defined and the parameter does not have a `Default` property, a KeyError will be thrown with a message like `Missing config_application_key_name variable for ApplicationKeyName input.  Please define this variable or specify a 'Default' property for the input`
- The `config_` prefix can be overridden by setting the `cf_config_prefix` variable

For example given the following stack template snippet:

```
...
...
Parameters:
  ApplicationImageId:
    Type: String
    Description: Application Amazon Machine Image Id
  ApplicationInstanceType:
    Type: String
    Description: Application EC2 Instance Type
    Default: t2.micro
    AllowedValues:
      - t2.micro
      - t2.small
      - t2.medium
      - t2.large
      - m4.large
  ApplicationAutoscalingDesiredCount:
    Type: Number
    Description: Application AutoScaling Group Desired Count
...
...
```

By default the template generator will look for the following variables which MUST be defined:

- `config_application_image_id`
- `config_application_autoscaling_desired_count`

The template generator will also look for the following optional variables:

- `config_application_instance_type` - if not defined, defaults to `t2.micro`

If you wish to disable this behaviour, you can explicitly define the `cf_stack_inputs` variable in your `groups_vars/all/vars.yml` settings:

```
cf_stack_name: Jenkins

# This is the equivalent autogenerated behavior
cf_stack_inputs:
  ApplicationImageId: "{{ config_application_image_id }}"
  ApplicationInstanceType: "{{ config_application_instance_type | default('t2.micro') }}"
  ApplicationAutoscalingDesiredCount: "{{ config_application_autoscaling_desired_count }}"
```

### S3 Template Upload

The S3 template upload feature is enabled by default, but can be disabled if required by setting the variable `cf_upload_s3` to `false`.

The `stack.json` template will be uploaded to an S3 bucket as defined by the variable `cf_s3_bucket`.

### Generating a Template Only

You can generate a template only by passing the tag `generate` to this role.  This will only create the templates as described above, but not attempt to create or update the stack in CloudFormation.

`ansible-playbook site.yml -e env=dev --tags generate`

Note the generated template will be uploaded to S3 as described earlier.

### Temporarily Disabling Stack Policy

You can temporarily disable the stack policy for a provisioning run by setting the variable `cf_disable_stack_policy` to true:

`ansible-playbook site.yml -e env=prod -e cf_disable_stack_policy=true`

This will set to the stack policy to the following policy before stack modification:

```
{
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : "Update:*",
        "Principal": "*",
        "Resource" : "*"
      }
    ]
  }
```

And then after stack modification is complete, reset the stack policy to it's previous state.

> Note: This role will also reset the stack policy in the event of a stack modification failure

### Role Facts

This role sets the following facts that you can use subsequently in your roles:

- `cloudformation['<stack-name>']` - CloudFormation facts about the created stack.  This includes stack resources and stack outputs.
- `cf_stack_facts` - CloudFormation facts about the created stack.  This includes stack resources and stack outputs and is identical to the `cloudformation['<stack-name>']` fact.
- `cf_s3_template_url` - S3 URL of the CloudFormation template.  This is also printed at the end of the completion of this role.

## Macros

This role includes Jinja macros which can automatically generate CloudFormation resources using common conventions and patterns.

Macros are located in the [`macros`](./macros) folder and create resources and outputs for various resource types.

Macros are structured according to the following conventions:

- Separate files exist for each resource category or type.  For example, the `network.j2` macros create all networking related resources and outputs according to a set of standard conventions.

- Each macro file defines a resources macro, which will create resources based upon a set of zero or more inputs.

- Each macro file optionally defines an outputs macro, which will create CloudFormation outputs based upon a set of zero or more inputs.

Current resource types supported include:

- Network - defined in [`network.j2`](./macros/network.j2).  This creates resources and outputs for creating all standard networking resources and outputs.

### Using Macros

To use macros, include the following declaration at the top of your CloudFormation template (i.e. `templates/stack.yml.j2`):

```
{% import 'macros/network.j2' as network with context %}
...
...
```

You can then call macros via the `network` variable in the example above:

```
{% import 'macros/network.j2' as network with context %}
...
...
Resources:
{{ network.resources(config_vpc_id, config_vpc_cidr, config_vgw_id) }}

Outputs:
{{ network.outputs(config_vpc_id, config_vpc_cidr) }}
...
```

## Examples

### Invoking the Role

The following is an example of a playbook configured to use this role.  Note the use of the [AWS STS role](git@github.com:Casecommons/aws-sts.git) to obtain STS credentials is separate from this role.

```
---
- name: STS Assume Role Playbook
  hosts: "{{ env }}"
  gather_facts: no
  environment:
  vars:
    sts_role_arn: "arn:aws:iam::123456789:role/admin"
    sts_role_session_name: testAssumeRole
    sts_region: us-west-2
  roles:
  - aws_sts

- name: Stack Deployment Playbook
  hosts: "{{ env }}"
  environment: "{{ sts_creds }}"
  roles:
    - aws-cloudformation
```

## Release Notes

### Version 0.9.4

- **BUG FIX** : Removed jinja references to Stack.Name in template s3.yml.j2 since it is redundant and susceptible to breakage `./templates/s3.yml/j2`

### Version 0.9.3

- **NEW FEATURE** : Added generic [cloudfront template](`https://github.com/Casecommons/aws-cloudformation/pull/2`)
- - **NEW FEATURE** : Added generic [s3 template](`https://github.com/Casecommons/aws-cloudformation/pull/4`)
- - **ENHANCEMENT** : Updated jinja indentation on [ecr template](`https://github.com/Casecommons/aws-cloudformation/pull/4`)
- - **NEW FEATURE** : Added generic [dns template](`https://github.com/Casecommons/aws-cloudformation/pull/7`)
- - **NEW FEATURE** : Added generic CA [certificate template](`https://github.com/Casecommons/aws-cloudformation/pull/9`)


### Version 0.9.2

- **BUG FIX** : Output `config.json` with all values as strings (required for CodePipeline CloudFormation deployment support)

### Version 0.9.1

- **ENHANCEMENT** : Support list of default dependency mappings in stack transform feature
- **BUG FIX** : Fix issue where DependsOn property renaming for stack transform resource fails if component resource does not having existing DependsOn property

### Version 0.9.0

- **NEW FEATURE** : Added stack transforms, a new feature to support merging component templates into a master template
- **NEW FEATURE** : Added stack overrides, a new syntax to override portions of the stack template
- **BREAKING CHANGE** : Auto generated stack inputs now rely on the `Stack.Inputs` dictionary, and support the same dot notation naming scheme of stack overrides
- **ENHANCEMENT**: Add S3 bucket name exports to [CloudFormation template](`templates/cfn.yml.j2`)

### Version 0.8.0

- **NEW FEATURE** : Auto generate stack inputs from CloudFormation template parameters
- **NEW FEATURE** : Add ability to disable stack rollback

### Version 0.7.0

- **NEW FEATURE** : Add [security template](`templates/security.yml.j2`)
- **BUG FIX** : Fix harded coded AZ count in [network template](`templates/network.yml.j2`)
- **ENHANCEMENT** : Add ability to specify AZ count in [proxy template](`templates/proxy.yml.j2`)
- **ENHANCEMENT** : Use native CloudFormation log group resorces in [proxy template](`templates/proxy.yml.j2`)

### Version 0.6.1

- **ENHANCEMENT** : Update [proxy template](`templates/proxy.yml.j2`) autoscaling update policy to match input desired count
- **ENHANCEMENT** : Add whitelist support for [proxy template](`templates/proxy.yml.j2`)
- **ENHANCEMENT** : Add disable whitelist support for [proxy template](`templates/proxy.yml.j2`)
- **ENHANCEMENT** : Add support for VPC Flow Logs to [network template]('templates/network.yml.j2')

### Version 0.6.0

- **ENHANCEMENT** : Output `config.json` build artifact compatible with AWS CodePipeline CloudFormation Deployment
- **ENHANCEMENT** : Add support for configuring public and/or private route 53 zones to [network template](`templates/network.yml.j2`)

### Version 0.5.0

- **ENHANCEMENT** : Add KMS key to [CloudFormation template](`templates/cfn.yml.j2`)

### Version 0.4.0

- **ENHANCEMENT** : Add `cf_stack_facts` output
- **BUG FIX** : Fix missing substituion in proxy template

### Version 0.3.1

- **BUG FIX** : Set Proxy template ELB idle timeout to 120 seconds to avoid ECS agent disconnections

### Version 0.3.0

- **ENHANCEMENT** : Add proxy stack template
- **ENHANCEMENT** : Add support for creating a default VPC domain in network template
- **ENHANCEMENT** : Add CloudFormation resources template

### Version 0.2.0

- **ENHANCEMENT** : Add EC2 Container Registry (ECR) template

### Version 0.1.1

- **BUG FIX** : Fix issue where playbook will exit with success code even if a failure occurs
- **ENHANCEMENT** : Add Subnet CIDRs as exported outputs

### Version 0.1.0

- First Release

## License

Copyright (C) 2017.  Case Commons, Inc.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

See www.gnu.org/licenses/agpl.html
