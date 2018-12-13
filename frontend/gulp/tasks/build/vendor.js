'use strict';

// Build the vendor JS bundle
const gulp      = require('gulp'),
    browserify  = require('browserify'),
    buffer      = require('vinyl-buffer'),
    config      = require('../../config.json'),
    source      = require('vinyl-source-stream')
;

const pkg = require('../../../package.json');
const deps = Object.keys(pkg.dependencies);

gulp.task('build.vendor', function() {
    const b = browserify({});

    b.require(deps);

    return b
        .bundle()
        .pipe(source('vendor.js'))
        .pipe(buffer())
        .pipe(gulp.dest(config.build + '/js'));
});
