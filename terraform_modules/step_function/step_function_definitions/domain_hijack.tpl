{
    "Comment": "Hijack workflow to track, alert, and remediate potential domain hijacks",
    %{ if init != "" ~}
    "StartAt": "Init",
    %{ else ~}
    "StartAt": "Resource Has Been Remediated",
    %{ endif ~}
    "States": {
        %{ if init != "" ~}
        "Init": {
            "Type": "Task",
            "Resource": "${init}",
            "Next": "Track or Analyze For Hijack"
        },
        "Track or Analyze For Hijack": {
            "Type": "Choice",
            "Choices": [
                {
                    "Or": [
                        {
                            "Variable": "$.Resource.EventName",
                            "StringEquals": "CreateHostedZone"
                        },
                        {
                            "Variable": "$.Resource.EventName",
                            "StringEquals": "ChangeResourceRecordSets"
                        }
                    ],
                    "Next": "Update DNS Hijack Resource Graph"
                },
                {
                    "Not": {
                        "Variable": "$.Resource.EventName",
                        "StringEquals": ""
                    },
                    "Next": "Resource Has Been Remediated"
                }
            ]
        },
        "Update DNS Hijack Resource Graph": {
            "Type": "Task",
            "Resource": "${graph_updater}",
            "Next": "Resource Has Been Remediated"
        },
        %{ endif }
        "Resource Has Been Remediated": {
            "Type": "Succeed"
        }
    }
}