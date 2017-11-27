'use strict';

// Copy third-party libs
const gulp  = require('gulp'),
    config  = require('../../config.json')
;

gulp.task('build.libs', function() {
    return gulp.src(config.libs)
        .pipe(gulp.dest(config.build + '/libs'));
});