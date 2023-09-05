(function() {
htmx.on('openNextChapterUrl', function(event) {
    window.open(event.detail.next_chapter_url, '__blank');
});
})()
