'use strict';

// Generate JSDocs
const gulp  = require('gulp'),
    config  = require('../../config.json'),
    jsdoc   = require('gulp-jsdoc3');

gulp.task('docs', function () {
    const docConf = {
        opts: {
            destination: './docs'
        },
        plugins: [
            "plugins/markdown"
        ]
    };
    const docPaths = ['./typedefs.js'].concat(config.javascript);
    return gulp.src(docPaths)
        .pipe(jsdoc(docConf));
});