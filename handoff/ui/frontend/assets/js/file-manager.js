$(function () {
    // https://js.devexpress.com/Documentation/Guide/UI_Components/FileManager/Bind_to_File_Systems/
    /*
    var provider = new DevExpress.fileManagement.RemoteFileSystemProvider({
        endpointUrl: "https://js.devexpress.com/Demos/Mvc/api/file-manager-file-system-images"
    });
    */
        // Assigns the Custom file system provider to the UI component
    customProvider = new DevExpress.fileManagement.CustomFileSystemProvider({
        // Function to get file system items
        getItems: getItems,
        // Functions to handle file operations
        createDirectory: createDirectory,
        deleteItem: deleteItem
        // ...
    });

    $("#file-manager").dxFileManager({
        name: "fileManager",
        fileSystemProvider: customProvider,
        currentPath: "Widescreen",
        permissions: {
            create: true,
            copy: true,
            move: true,
            delete: true,
            rename: true,
            upload: true,
            download: true
        },
		onSelectedFileOpened: function(e) {
            loadFile(e.file.key);
            /*
			var popup = $("#photo-popup").dxPopup("instance");
            popup.option({
                "title": e.file.name,
                "contentTemplate": "<img src=\"" + e.file.dataItem.url + "\" class=\"photo-popup-image\" />"
            });
            popup.show();
            */
		}
    });

    /*
    $("#photo-popup").dxPopup({
		maxHeight: 600,
        closeOnOutsideClick: true,
        onContentReady: function(e) {
            var $contentElement = e.component.content();  
            $contentElement.addClass("photo-popup-content");
          }
	});
    */
});
function getItems (pathInfo) {
    fetchProjectFiles();
    sleep(1000.0);
    if (pathInfo.dataItem !== undefined) {
        return pathInfo.dataItem.items;
    }
    return getProjectFiles(pathInfo);
}
function createDirectory(parentDirectory, name) {
    // your code
}
function deleteItem(item) {
    // your code
}