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
            "Next": "Evauluate Each Resource"
        },
        "Evauluate Each Resource": {
            "Type": "Map",
            "InputPath": "$",
            "ItemsPath": "$.resources",
            "MaxConcurrency": 1,
            "Iterator": {
                "StartAt": "Track or Analyze For Hijack",
                "States": {
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
                                        "And": [
                                            {
                                                "Variable": "$.Resource.EventName",
                                                "StringEquals": "ChangeResourceRecordSets"
                                            }, 
                                            {
                                                "Variable": "$.Resource.Action",
                                                "StringEquals": "CREATE"
                                            }
                                        ]
                                    },
                                    {
                                        "Variable": "$.Resource.EventName",
                                        "StringEquals": "CreateDistribution"
                                    }
                                ],
                                "Next": "Update DNS Hijack Resource Graph"
                            },
                            {
                                "And": [
                                    {
                                        "Variable": "$.Resource.EventName",
                                        "StringEquals": "ChangeResourceRecordSets"
                                    }, 
                                    {
                                        "Variable": "$.Resource.Action",
                                        "StringEquals": "UPSERT"
                                    }
                                ],
                                "Next": "Track and Analyze for Hijack"
                            }
                        ],
                        "Default": "End of iterator"
                    },
                    "Update DNS Hijack Resource Graph": {
                        "Type": "Task",
                        "Resource": "${graph_updater}",
                        "End": true
                    },
                    "Track and Analyze for Hijack": {
                        "Type": "Parallel",
                        "End": true,
                        "Branches": [
                            {
                                "StartAt": "Update DNS Hijack Resource Graph - Parallel",
                                "States": {
                                    "Update DNS Hijack Resource Graph - Parallel": {
                                        "Type": "Task",
                                        "Resource": "${graph_updater}",
                                        "End": true
                                    }
                                }
                            }
                        ]
                    },
                    "End of iterator" : {
                        "Type": "Pass",
                        "End": true
                    }
                }
            },
            "ResultPath": "$.resources_completed",
            "Next": "Resource Has Been Remediated"
        },
        %{ endif }
        "Resource Has Been Remediated": {
            "Type": "Succeed"
        }
    }
}

