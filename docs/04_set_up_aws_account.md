## Setting up an AWS account and profile

handoff helps you to deploy the task in the cloud computing services.
Our goal in this tutorial is to deploy the currency exchange
rates task to [AWS Fargate](https://aws.amazon.com/fargate/).

Before we can deploy, we need to set up the AWS account.



**Do I need a credit card to use AWS? How much does it cost?**

Yes, you need a credit card. But it won't cost a cup of coffee for this tutorial.
(Probably not even a dollar.)
Some of the AWS services we use comes with a Free Tier and you won't be
charged for the eligible usage.

Learn more about [Free Tier](https://aws.amazon.com/free).



Here is the complete list of the services we use:

- Simple Storage Service, free with Free Tier usage:
    https://aws.amazon.com/s3/pricing/#AWS_Free_Tier
- Fargate, almost free:
    Price calculator http://fargate-pricing-calculator.site.s3-website-us-east-1.amazonaws.com/
    (We use 0.25vCPU with 0.5GB RAM for less than 5 minutes.)
- Systems Management Parameter Store, free (Standard tier):
    Pricing: https://aws.amazon.com/systems-manager/pricing/#Parameter_Store
- Elastic Container Registry, free for 500MB per month
    Pricing: https://aws.amazon.com/ecr/pricing/



AWS sign up is easy. Just go to:

    https://aws.amazon.com/free
    
and complete the sign up process.

The rest of the tutorial assumes that you have an active AWS account.



If you haven't, install AWS CLI (command line interface):

    https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html



Also generate access key ID and secret access key by following:

    https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#xxxxxxxxds

Take note of the values that looks like:

- Access key ID: AKIAIOSFODNN7EXAMPLE
- Secret access key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

The only time that you can view or download the secret access key is when you
create the keys. You cannot recover them later. So keep a local copy.



Last step before going back to handoff. From the console, run:

    aws configure --profile default

Enter Access key ID and Secret access key you created in the last step.

For region, use one of these keys (for USA users, us-east-1 would do):


```shell

ap-northeast-1
ap-northeast-2
ap-northeast-3
ap-south-1
ap-southeast-1
ap-southeast-2
ca-central-1
eu-central-1
eu-north-1
eu-west-1
eu-west-2
eu-west-3
sa-east-1
us-east-1
us-east-2
us-west-1
us-west-2
```

Learn more about AWS profile
[here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html)



Now that we have set up the AWS account, let's store the configurations
in the cloud in the next section.

