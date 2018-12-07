'use strict';

// Cleanup dist folder
const gulp  = require('gulp'),
    config  = require('../../config.json'),
    clean   = require('gulp-clean')
;

gulp.task('cleanup', function() {
    return gulp.src(config.build, {read: false})
        .pipe(clean());
});