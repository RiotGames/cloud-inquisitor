describe('UI loads and basic login redirect happens', function() {
    it('should have visible UI elements', function() {
        browser.get(browser.params.auditsUrl);
        expect(browser.getTitle()).toEqual('Cloud Inquisitor');
    });
});

