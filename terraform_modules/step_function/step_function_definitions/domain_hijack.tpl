{
    "Comment": "Hijack workflow to track, alert, and remediate potential domain hijacks",
    %{ if dns_hijack_init != "" ~}
    "StartAt": "Init",
    %{ else ~}
    "StartAt": "Resource Has Been Remediated",
    %{ endif ~}
    "States": {
        %{ if dns_hijack_init != "" ~}
        "Init": {
            "Type": "Task",
            "Resource": "${dns_hijack_inti}",
            "Next": "Resource Has Been Remediated"
        },
        %{ endif }
        "Resource Has Been Remediated": {
            "Type": "Succeed"
        }
    }
}