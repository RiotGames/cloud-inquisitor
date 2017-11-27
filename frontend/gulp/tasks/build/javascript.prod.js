'use strict';

// Build and minify javascript application
const gulp      = require('gulp'),
    babelify    = require('babelify'),
    browserify  = require('browserify'),
    buffer      = require('vinyl-buffer'),
    config      = require('../../config.json'),
    ngAnnotate  = require('gulp-ng-annotate'),
    source      = require('vinyl-source-stream'),
    sourcemaps  = require('gulp-sourcemaps'),
    uglify      = require('gulp-uglify')
;

const pkg = require('../../../package.json');
const deps = Object.keys(pkg.dependencies);

gulp.task('build.javascript.prod', function () {
    return browserify(config.app)
        .transform("babelify", {presets: ['es2015']})
        .external(deps)
        .bundle()
        .pipe(source('bundle.js'))
        .pipe(buffer())
        .pipe(sourcemaps.init({loadMaps: true}))
        .pipe(ngAnnotate())
        .pipe(uglify())
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest(config.build + '/js'));
});