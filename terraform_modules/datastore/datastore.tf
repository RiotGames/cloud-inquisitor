resource "random_password" "password" {
  length = 24
  special = false
}

resource "aws_db_instance" "datastore" {
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "mysql"
  engine_version       = "8.0"
  auto_minor_version_upgrade = true
  instance_class       = "db.t2.micro"
  identifier = "${var.environment}-${replace(var.name, "_", "-")}-datastore-${var.region}-${replace(var.version_str, "_","-")}"
  name                 = var.datastore_database_name
  username             = "cloudinquisitor"
  password             = random_password.password.result
  db_subnet_group_name = aws_db_subnet_group.datastore_subnet.name
  vpc_security_group_ids = [
      aws_security_group.mysql_tcp.id
  ]
  tags = var.datastore_tags
  skip_final_snapshot = var.skip_final_snapshot
  final_snapshot_identifier = "${var.environment}-${replace(var.name, "_", "-")}-datastore-${var.region}-${replace(var.version_str, "_","-")}-final-snapshot"
}

resource "aws_db_subnet_group" "datastore_subnet" {
    name = "${var.environment}_${var.name}_datastore_subnet_${var.region}_${var.version_str}"
    subnet_ids = var.datastore_subnets
}

resource "aws_security_group" "mysql_tcp" {
    name = "${var.environment}-${replace(var.name, "_", "-")}-mysql-port-${var.region}-${replace(var.version_str, "_","-")}"
    vpc_id = var.datastore_vpc

    ingress {
        from_port = 3306
        to_port = 3306
        protocol = "tcp"
        cidr_blocks = var.datastore_connection_cidr
    }

    /*egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }*/
}