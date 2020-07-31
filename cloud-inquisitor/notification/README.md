Testing the Notification Module
=================================

There are two type of tests contained in this module.

Unit tests can be ran normally and expected to pass in any condition.

The included funtional tests require a user to have active AWS credentials that give the user AWS SES access. This will allow the AWS SES Notifier to be tested and manually validated.

The functional tests can be ran with:

```bash
go test -v --tags functional
```
