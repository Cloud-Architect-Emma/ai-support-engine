resource "aws_dynamodb_table" "orders" {
  name         = "orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "users" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "support_logs" {
  name         = "support_logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "log_id"

  attribute {
    name = "log_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "complaints" {
  name         = "complaints"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "complaint_id"

  attribute {
    name = "complaint_id"
    type = "S"
  }
}
