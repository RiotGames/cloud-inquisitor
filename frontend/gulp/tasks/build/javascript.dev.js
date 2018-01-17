'use strict';

// Build javascript application, but don't minify it
const gulp      = require('gulp'),
    babelify    = require('babelify'),
    browserify  = require('browserify'),
    buffer      = require('vinyl-buffer'),
    config      = require('../../config.json'),
    source      = require('vinyl-source-stream'),
    sourcemaps  = require('gulp-sourcemaps')
;

const pkg = require('../../../package.json');
const deps = Object.keys(pkg.dependencies);

gulp.task('build.javascript.dev', function () {
    return browserify(config.app)
        .transform("babelify", {
            presets: [['env', {
                "targets": {
                    "chrome": "60"
                }
            }]]
        })
        .external(deps)
        .bundle()
        .pipe(source('bundle.js'))
        .pipe(buffer())
        .pipe(sourcemaps.init({loadMaps: true}))
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest(config.build + '/js'));
});
