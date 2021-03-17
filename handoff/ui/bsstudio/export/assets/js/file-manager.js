var provider = [
    {
        name: "Documents",
        isDirectory: true,
        items: [
            {
                name: "Projects",
                isDirectory: true,
                items: [
                    {
                        name: "About.rtf",
                        isDirectory: false,
                        size: 1024
                    },
                    {
                        name: "Passwords.rtf",
                        isDirectory: false,
                        size: 2048
                    }
                ]
            },
            {
                name: "About.xml",
                isDirectory: false,
                size: 1024
            },
            {
                name: "Managers.rtf",
                isDirectory: false,
                size: 2048
            },
            {
                name: "ToDo.txt",
                isDirectory: false,
                size: 3072
            }
        ],
    },
    {
        name: "Images",
        isDirectory: true,
        items: [
            {
                name: "logo.png",
                isDirectory: false,
                size: 20480
            },
            {
                name: "banner.gif",
                isDirectory: false,
                size: 10240
            }
        ]
    },
    {
        name: "System",
        isDirectory: true,
        items: [
            {
                name: "Employees.txt",
                isDirectory: false,
                size: 3072
            },
            {
                name: "PasswordList.txt",
                isDirectory: false,
                size: 5120
            }
        ]
    },
    {
        name: "Description.rtf",
        isDirectory: false,
        size: 1024
    },
    {
        name: "Description.txt",
        isDirectory: false,
        size: 2048
    }
];

$(function () {
    // https://js.devexpress.com/Documentation/Guide/UI_Components/FileManager/Bind_to_File_Systems/
    /*
    var provider = new DevExpress.fileManagement.RemoteFileSystemProvider({
        endpointUrl: "https://js.devexpress.com/Demos/Mvc/api/file-manager-file-system-images"
    });
    */
    /*
        // Assigns the Custom file system provider to the UI component
    fileSystemProvider: new DevExpress.fileManagement.CustomFileSystemProvider({
        // Function to get file system items
        getItems: getItems,
        // Functions to handle file operations
        createDirectory: createDirectory,
        deleteItem: deleteItem
        // ...
    }), 
    */

    $("#file-manager").dxFileManager({
        name: "fileManager",
        fileSystemProvider: provider,
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
			var popup = $("#photo-popup").dxPopup("instance");
            popup.option({
                "title": e.file.name,
                "contentTemplate": "<img src=\"" + e.file.dataItem.url + "\" class=\"photo-popup-image\" />"
            });
            popup.show();
		}
    });

    $("#photo-popup").dxPopup({
		maxHeight: 600,
        closeOnOutsideClick: true,
        onContentReady: function(e) {
            var $contentElement = e.component.content();  
            $contentElement.addClass("photo-popup-content");
          }
	});
});
function getItems (pathInfo) {
    // your code
}
function createDirectory(parentDirectory, name) {
    // your code
}
function deleteItem(item) {
    // your code
}