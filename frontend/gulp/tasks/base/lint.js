'use strict';

// Run lint-checks on Javascript code
const gulp      = require('gulp'),
    config      = require('../../config.json'),
    lint        = require('gulp-jscs'),
    jshint      = require('gulp-jshint'),
    stylish     = require('jshint-stylish')
;

gulp.task('lint', function() {
    return gulp.src(config.javascript)
        .pipe(lint())
        .pipe(lint.reporter())
        .pipe(jshint())
        .pipe(jshint.reporter('jshint-stylish'));
});