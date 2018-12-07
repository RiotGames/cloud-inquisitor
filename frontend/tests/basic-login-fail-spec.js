
describe('UI loads, redirects to basic login, and backend is up', function() {
    afterEach(function () {
        // global variable we should reset
        browser.ignoreSynchronization = false;
    });
    it('follow redirect and login to backend with bad password', function() {
        browser.get(browser.params.auditsUrl);

        expect(browser.getTitle()).toEqual('Cloud Inquisitor');
        element(by.id('input_0')).sendKeys('admin');
        element(by.id('input_1')).sendKeys('badpassword');
        element(by.css('button[type="submit"]')).click();

        // don't wait for all angular bits to resolve. Allows testing of temporary notification pop-up.
        browser.ignoreSynchronization = true;
        browser.sleep(1000);

        var toastAlert = element(by.css('md-toast'));
        expect(toastAlert.isDisplayed()).toBe(true);
        expect(toastAlert.getText()).toContain('Invalid user or password');
    });
});

