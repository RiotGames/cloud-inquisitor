exports.config = {
    params: {
        auditsUrl: 'https://localhost'
    },
    specs: ['ui-loads-spec.js', 'basic-login-fail-spec.js'],
    multiCapabilities: [
        {'browserName': 'chrome'},
        // {'browserName': 'firefox'},
        // PhantomJS doesn't work well with angular framework.
    ]
};
