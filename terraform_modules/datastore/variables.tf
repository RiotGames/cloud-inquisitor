variable "name" {
    type = string
}

variable "environment" {
    type = string
}

variable "region" {
    type = string
}

variable "version_str" {
    type = string
}

variable "skip_final_snapshot" {
    type = bool
    default = false
}

variable "datastore_database_name" {
    type = string
    default = "cloudinquisitor"
}

variable "datastore_vpc" {
    type = string
}

variable "datastore_subnets" {
    type = list(string)
    description = "list of subnet ids to deploy datastore to"
}

variable "datastore_connection_cidr" {
    type = list(string)
}

variable "datastore_tags" {
    type = map(string)
    description = "map of tags to apply to all data store resources"
}

output "connection_string"  {
    value = "${aws_db_instance.datastore.username}:${random_password.password.result}@tcp(${aws_db_instance.datastore.address})/${var.datastore_database_name}"
}

