{
    "Comment": "Hijack workflow to track, alert, and remediate potential domain hijacks",
    "StartAt": "Init",
    "States": {
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
                "StartAt": "Analyze for Hijack",
                "States": {
                    "Analyze for Hijack": {
                        "Type": "Task",
                        "Resource": "${graph_analyzer}",
                        "Next": "Track Resource Changes"
                    },
                    "Track Resource Changes": {
                        "Type": "Task",
                        "Resource": "${graph_updater}",
                        "End": true
                    }
                }
            },
            "ResultPath": "$.resources_completed",
            "Next": "Resource Has Been Remediated"
        },
        "Resource Has Been Remediated": {
            "Type": "Succeed"
        }
    }
}

