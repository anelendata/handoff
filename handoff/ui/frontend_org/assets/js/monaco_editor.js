// https://www.npmjs.com/package/monaco-vim
require.config({ 
    paths: { 
        'vs': 'https://unpkg.com/monaco-editor@0.17.1/min/vs',
        'monaco-vim': 'https://unpkg.com/monaco-vim/dist/monaco-vim'
    }});        
window.MonacoEnvironment = { getWorkerUrl: () => proxy };

let proxy = URL.createObjectURL(new Blob([`
	self.MonacoEnvironment = {
		baseUrl: 'https://unpkg.com/monaco-editor0.17.1/min/'
	};
	importScripts('https://unpkg.com/monaco-editor@0.17.1/min/vs/base/worker/workerMain.js');
`], { type: 'text/javascript' }));

require(["vs/editor/editor.main",
         'monaco-vim'
        ], function (a, MonacoVim) {
	let editor = monaco.editor.create(document.getElementById('monaco-editor'), {
		value: [
			'# yaml'
		].join('\n'),
		language: 'yaml',
		theme: 'vs'
	});
    var statusNode = document.getElementById('editor-status');
    var vimMode = MonacoVim.initVimMode(editor, statusNode);
});