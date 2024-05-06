## pip

This is the standard package installer for Python. It allows you to install and manage additional libraries and dependencies that are not included in the standard Python library.

## requirements.txt

This file is akin to package.json in Node.js. It lists all of the packages your project needs. You can generate it by manually writing the package names along with versions, or by using pip freeze after installing the packages in your local environment.

## virtualenv/venv

These are tools to create isolated Python environments. Each environment has its own Python binary and can have its own independent set of installed Python packages. This is similar to having a node_modules folder in Node.js that isolates dependencies per project.

### To create the venv: `python -m venv venv`

-m:
This flag tells Python to run the following module as a script. It allows you to use modules that are part of the standard library or are installed in site-packages as scripts.

venv:
This is the module that will be run as a script. venv is a module that comes with Python (from version 3.3 onwards), which creates virtual environments.

The second venv (**_the node_modules folder_**):
This is the name of the directory where the virtual environment will be created. It's a common convention to name this directory venv, but it could be named anything. This directory will contain a copy of the Python interpreter, the standard library, and various supporting files.

**_Generally want to add the venv folder to your .gitignore file_**

### To activate the virtual environment:

```
On Windows: venv\Scripts\activate
On Unix or MacOS: source venv/bin/activate
```

Activating the virtual environment adjusts several environment variables:

PATH: Prepends the virtual environment’s bin directory to the environment variable PATH. This means that when you invoke Python or other tools like pip, the shell finds them in the virtual environment's bin directory first, rather than somewhere else on your system.

VIRTUAL_ENV: Sets this environment variable to the path of the virtual environment, which can be useful for scripts to check if one is active.

PS1 (optionally): Changes your shell prompt to include the name of the virtual environment, making it clear which environment is active (this is more visual feedback than functional).

Essentially, activating a virtual environment ensures that:

- You use the Python interpreter specific to that environment.
- Any Python libraries you install while the environment is active are placed in the environment’s directory, isolated from the global Python environment.
- Any commands you run that use Python will operate with the environment’s Python interpreter and site packages.

## Installing dependencies

To add a dependency to the venv, use `pip install <pkg1> <pkg2> ...`
e.g. `pip install requests flask`

To save it to the requirements.txt use:
`pip freeze > requirements.txt`

To install dependencies from the requirements file:
`pip install -r requirements.txt`

## Package the function and all its dependencies for Lambda

1. Create a new directory for packaging:

This directory will hold your Python script and all the necessary dependencies.

```bash
mkdir package
```

2. Install dependencies into the packaging directory:

You use the -t or --target option with pip to install packages into a specified directory.

```bash
pip install -r requirements.txt -t package/
```

3. Add your Python script to the packaging directory:

You need to copy or move your handler.py file into this directory.

```bash
cp handler.py package/
```

4. Navigate to the packaging directory:

Before creating the zip file, switch to the packaging directory.

```bash
cd package
```

5. Create the zip file:

Use the zip command to create a zip archive of your Lambda function and dependencies. Make sure to include hidden files and directories if any.

```bash
zip -r ../lambda_function.zip .
```

Here, -r stands for recursive, so it includes all subdirectories and files. The . at the end of the command indicates that all files and directories in the current directory should be added to the zip file.

6. Move the zip file to a desired location (optional):

If you want to move your zip file to a specific directory or just to the root of your project for easier access, you can do that:

```bash
mv ../lambda_function.zip /path/to/your/desired/location
```

## Transitioning to containerization

- No Need to Deactivate: You don’t necessarily have to deactivate your virtual environment before running Docker commands because Docker doesn’t interact with it. Docker builds an image based on the instructions in the Dockerfile, and these instructions run in the isolated context of the Docker build process.

- Ignore the Venv Directory: Ensure your Dockerfile doesn’t copy over the virtual environment directory. This is typically handled by your .gitignore and .dockerignore files:

```plaintext
# .dockerignore
venv/
```

## Containerize the function and all its dependencies for Lambda

1. Create the DOckerfile

```dockerfile
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "handler.main" ]
```

2. Build and Run the docker image locally

```bash
docker build --platform linux/arm64 -t docker-image:test .
```

```bash
docker run --platform linux/arm64 -p 9000:8080 docker-image:test
```

This command runs the image as a container and creates a local endpoint at localhost:9000/2015-03-31/functions/function/invocations.

Note:
These commands specifies the --platform linux/amd64 option to ensure that your container is compatible with the Lambda execution environment regardless of the architecture of your build machine. If you intend to create a Lambda function using the ARM64 instruction set architecture, be sure to change the command to use the --platform linux/arm64 option instead.

If you built the Docker image for the ARM64 instruction set architecture, be sure to use the --platform linux/arm64 option instead of --platform linux/amd64.

From a new terminal window, post an event to the local endpoint.

```bash
curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"event":"hello world!", "context":"hello world!"}'
```

3. Login to ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 111122223333.dkr.ecr.us-east-1.amazonaws.com
```

4. Create and ECR repo

```bash
aws ecr create-repository --repository-name hello-world --region us-east-1 --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE
```

Record the ECR repositoryUri from the output.

5. Tag the docker image

```bash
docker tag docker-image:test <ECRrepositoryUri>:latest
```

6. Push the docker image

```bash
docker push 111122223333.dkr.ecr.us-east-1.amazonaws.com/hello-world:latest
```

Record the ImageUri from the output.

7. Create a Lambda Execution Role for the function

You need the Amazon Resource Name (ARN) of the role. See here for details:
https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-awscli.html#with-userapp-walkthrough-custom-events-create-iam-role

8. Create the Lambda Function

For ImageUri, specify the repository URI from earlier. Make sure to include :latest at the end of the URI.

```bash
aws lambda create-function \
  --function-name hello-world \
  --package-type Image \
  --code ImageUri=111122223333.dkr.ecr.us-east-1.amazonaws.com/hello-world:latest \
  --role arn:aws:iam::111122223333:role/lambda-ex
```

9. Invoke the function

```bash
aws lambda invoke --function-name hello-world response.json
```

To see the output of the function, open the response.json file.

## Containerize vs Zip

Pros and Cons of Containerizing Lambda Functions
Pros:

- Consistency and Reliability: Container images provide a consistent environment for your application, from local development through to production. This reduces the "it works on my machine" problem, where code behaves differently in different environments.

- Control Over the Environment: Containers allow you to specify the exact versions of the underlying OS, system libraries, and language runtime. This is particularly useful for dependencies that require specific system libraries or need a particular runtime environment.

- Ease of Dependency Management: You can manage dependencies in a way that is isolated from the host system, reducing conflicts between projects and simplifying setup for new developers or in new environments.

- Integration with Modern DevOps: Containerized applications fit well into modern development pipelines and platforms that support Docker, such as Kubernetes, Amazon ECS, and more.

Cons:

- Larger Size: Container images are typically larger than zipped deployment packages because they include the complete file system required to run your application, including the OS and runtime.

- Complexity: Building and managing containers can add complexity to your deployment process, especially if you are not already familiar with container technologies.

- Performance Overhead: While minimal, there is some performance overhead associated with running applications in containers due to the additional layer of abstraction.

## A Note about Layers

Layers is a way to share common dependancies across multiple Lambda functions.

- Lambda charges $0.10 per GB-month
- The code size within the layer contributes to the overall size of your Lambda deployment package
