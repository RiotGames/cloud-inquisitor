'use strict';

// Build and minify javascript application
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

gulp.task('build.javascript.prod', function () {
    return browserify(config.app)
        .transform("babelify", {
            presets: [
                ['env', {
                    "targets": {
                        "chrome": "60"
                    }
                }],
                "minify"
            ],
            plugins: ["angularjs-annotate"]
        })
        .external(deps)
        .bundle()
        .pipe(source('bundle.js'))
        .pipe(buffer())
        .pipe(sourcemaps.init({loadMaps: true}))
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest(config.build + '/js'));
});
