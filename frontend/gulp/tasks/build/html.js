'use strict';

// Minify HTML code
const gulp      = require('gulp'),
    config      = require('../../config.json'),
    htmlmin     = require('gulp-htmlmin'),
    tmplCache   = require('gulp-angular-templatecache')
;

gulp.task('build.html', function() {
    gulp.src(config.html)
        .pipe(htmlmin({
            collapseWhitespace: true,
            minifyCSS: true
        }))
        .pipe(gulp.dest(config.build));

    gulp.src(config.templates)
        .pipe(htmlmin({
            collapseWhitespace: true,
            minifyCSS: true
        }))
        .pipe(tmplCache({standalone: true}))
        .pipe(gulp.dest(config.build + '/js'));

    gulp.src(config.resources)
        .pipe(gulp.dest(config.build));
});
