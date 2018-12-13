'use strict';

// Generate CSS files from SCSS
const gulp      = require('gulp'),
    config      = require('../../config.json'),
    sass        = require('gulp-sass'),
    importer    = require('sass-module-importer')
;

const sassOptions = {
    outputStyle: 'compressed',
    importer: importer()
};

gulp.task('build.sass', function() {
    return gulp.src(config.css)
        .pipe(sass(sassOptions).on('error', sass.logError))
        .pipe(gulp.dest(config.build + '/css'));
});