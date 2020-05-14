{
    "Comment": "Tag Auditor that tracks a resource over N stages",
    "StartAt": "Init",
    "States": {
        "Init": {
            "Type": "Task",
            "Resource": "${tag_auditor_init}",
            "Next": "Wait For First Notification"
        },
        "Wait For First Notification" : {
            "Type": "Wait",
            "Seconds": ${init_seconds},
            "Next": "Fist Notification"
        },
        "First Notification": {
            "Type": "Task",
            "Resource": "${tag_auditor_notify}",
            "Next": "Wait For Second Notification"
        },
        "Wait For Second Notification" : {
            "Type": "Wait",
            "Seconds": ${first_notify_seconds},
            "Next": "Second Notification"
        },
        "Second Notification": {
            "Type": "Task",
            "Resource": "${tag_auditor_notify}",
            "Next": "Wait For Third Notification"
        },
        "Wait For Third Notification" : {
            "Type": "Wait",
            "Seconds": ${second_notify_seconds},
            "Next": "Third Notification"
        },
        "Third Notification": {
            "Type": "Task",
            "Resource": "${tag_auditor_notify}",
            "Next": "Wait For Prevent"
        },
        "Wait For Prevent" : {
            "Type": "Wait",
            "Seconds": ${prevent_seconds},
            "Next": "Prevent"
        },
        "Prevent": {
            "Type": "Task",
            "Resource": "${tag_auditor_prevent}",
            "Next": "Wait For Remove"
        },
        "Wait For Remove" : {
            "Type": "Wait",
            "Seconds": ${remove_seconds},
            "Next": "Remove"
        },
        "Remove": {
            "Type": "Task",
            "Resource": "${tag_auditor_remove}",
            "End": true
        }
    }
}