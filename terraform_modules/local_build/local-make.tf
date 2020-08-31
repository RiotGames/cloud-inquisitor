resource "null_resource" "local_machine" {

    provisioner "local-exec" {
        working_dir = var.working_dir
        command = <<CMD
    git clone -brance ${var.branch} https://github.com/RiotGames/cloud-inquisitor.git
    CMD
    }

}

variable "branch" {
    type = string
    description = "branch of the project to clone and build from"
    default = "master"
}

variable "working_dir" {
    type = string
    description = "path to clone repo into"
    default = "./"
}