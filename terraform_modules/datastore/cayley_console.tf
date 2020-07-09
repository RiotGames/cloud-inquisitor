locals {
    cayley_userdata = <<EOF
#!/bin/bash

echo "installing docker"
apt-get update
apt-get -y install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
apt-key fingerprint 0EBFCD88
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io
usermod -aG docker ubuntu

echo "installing cayley config"
mkdir -p /opt/cayley
cat << CAYLEY > /opt/cayley/cayley.yaml
store:
  backend: "mysql"
  address: "${aws_db_instance.datastore.username}:${random_password.password.result}@tcp(${aws_db_instance.datastore.address})/${var.datastore_database_name}"
CAYLEY

echo "starting cayley container"
docker run --rm -v /opt/cayley:/data cayleygraph/cayley -c /data/cayley.yaml http --init
docker run --rm -d -p 8080:64210 -v /opt/cayley:/data cayleygraph/cayley -c /data/cayley.yaml http
    EOF
}

resource "aws_instance" "cayley_console" {
    count = var.cayley_console
    ami = var.cayley_ami
    instance_type = "t2.micro"
    user_data_base64 = base64encode(local.cayley_userdata)
    subnet_id = var.cayley_subnet
    vpc_security_group_ids = [
        aws_security_group.cayley_ssh.id
    ]
    tags = merge(
        var.datastore_tags,
        {
            "Name": "${var.environment}-${replace(var.name, "_", "-")}-cayley_console-${var.region}-${replace(var.version_str, "_","-")}"
        }
    )
}

resource "aws_security_group" "cayley_ssh" {
    name = "${var.environment}-${replace(var.name, "_", "-")}-cayley-console-ssh-${var.region}-${replace(var.version_str, "_","-")}"
    vpc_id = var.cayley_vpc

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = var.cayley_ssh_cidr
    }

    ingress {
        from_port = 8080
        to_port = 8080
        protocol = "tcp"
        cidr_blocks = var.cayley_ssh_cidr
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

locals {
    cayley_instances = {
        for num,instance in aws_instance.cayley_console:
        num => {
            "id": instance.id,
            "ip": instance.private_ip
        }
    }
}