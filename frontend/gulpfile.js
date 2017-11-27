'use strict';

const gulp      = require('gulp'),
    lock        = require('gulp-lock'),
    notifier    = require('node-notifier'),
    requireDir  = require('require-dir'),
    runSequence = require('run-sequence'),
    watch       = require('gulp-watch'),
    util        = require('gulp-util')
;

requireDir('./gulp/tasks', { recurse: true });
const config = require('./gulp/config.json');
let buildlock = lock();

// Task to do development build, no JS minification here
gulp.task('build.dev', buildlock.cb(cb => {
    notifier.notify({
        title: 'Cloud Inquisitor',
        message: 'Cloud Inquisitor Build started',
        timeout: 3
    });

    return runSequence(
        'cleanup',
        'lint',
        [
            'build.vendor',
            'build.libs',
            'build.sass',
            'build.html',
            'build.javascript.dev'
        ],
        () => {
            notifier.notify({
                title: 'Cloud Inquisitor',
                message: 'Build complete',
                timeout: 3
            });
            cb();
        }
    );
}));

// Build production version of code, minified JS, CSS and HTML
gulp.task('build.prod', buildlock.cb(cb => {
    notifier.notify({
        title: 'Cloud Inquisitor',
        message: 'Cloud Inquisitor Build started',
        timeout: 3
    });

    return runSequence(
        'cleanup',
        'lint',
        [
            'build.vendor',
            'build.libs',
            'build.sass',
            'build.html',
            'build.javascript.prod'
        ],
        () => {
            notifier.notify({
                title: 'Cloud Inquisitor',
                message: 'Build complete',
                timeout: 3
            });
            cb();
        }
    );
}));

// Run in dev-mode building new files on changes
gulp.task('watch', () => {
    const paths = config.javascript
        .concat(config.html)
        .concat(config.css)
        .concat(config.libs)
        .concat(config.templates)
    ;

    util.log('Watching paths:');
    for (const p of paths) {
        util.log(util.colors.green('    ' + p));
    }

    return watch(
        paths,
        {
            usePolling: true,
            interval: 3000,
            binaryInterval: 3000
        },
        () => {
            return runSequence('build.dev')
        }
    );
});

// Combined dev task for building initial and then watching
gulp.task('dev', () => {
    return runSequence('build.dev', 'watch');
});


gulp.task('default', () => { gulp.start('build.prod'); });
