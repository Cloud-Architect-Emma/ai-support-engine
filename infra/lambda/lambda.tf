resource "aws_iam_role" "lambda_role" {
  name = "self_healing_support_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Add DynamoDB access
resource "aws_iam_role_policy" "lambda_dynamodb_access" {
  name = "lambda_dynamodb_access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "self_healing_support" {
  function_name = "self_healing_support_engine"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"

  filename         = "${path.module}/../../build/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../../build/lambda.zip")

  environment {
    variables = {
      DYNAMO_ORDERS_TABLE    = "orders"
      DYNAMO_USERS_TABLE     = "users"
      DYNAMO_LOGS_TABLE      = "support_logs"
      DYNAMO_COMPLAINTS_TABLE = "complaints"
    }
  }
}

output "lambda_arn" {
  value = aws_lambda_function.self_healing_support.arn
}
