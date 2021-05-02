var monacoVersion = '0.17.0';
var monacoUrl = 'https://unpkg.com/monaco-editor@' + monacoVersion + '/min/'
let editor;
// https://www.npmjs.com/package/monaco-vim
require.config({ 
    paths: { 
        'vs': monacoUrl + 'vs',
        'monaco-vim': 'https://unpkg.com/monaco-vim/dist/monaco-vim'
    }});        
window.MonacoEnvironment = { getWorkerUrl: () => proxy };

let proxy = URL.createObjectURL(new Blob([`
	self.MonacoEnvironment = {
		baseUrl: '` + monacoUrl + `'
	};
	importScripts('` + monacoUrl + `' + 'vs/base/worker/workerMain.js');
`], { type: 'text/javascript' }));

require(["vs/editor/editor.main",
         'monaco-vim'
        ],
        // function () {
        function (a, MonacoVim) {
	editor = monaco.editor.create(document.getElementById('monaco-editor'), {
		value: [
			''
		].join('\n'),
		language: 'yaml',
		theme: 'vs'
	});
    var statusNode = document.getElementById('editor-status');
    // var vimMode = MonacoVim.initVimMode(editor, statusNode);
});