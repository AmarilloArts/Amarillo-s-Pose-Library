# Amarillo's Pose Library

![](https://i.imgur.com/BTXVogT.gif)

What is this?
=============
This is my own take on the [deprecated Pose Library](https://blenderartists.org/t/pose-library-legacy/1457190) from Blender. I liked how simple and straightforward it was. It let me save and load poses much faster than the current Asset Library implementation, which I am not a fan of.

What features does it include?
==============================
### Fast use
Just one click to save, one click to load.

### Multiple armatures at the same time
I don't like having every component of a character in the same armature, so naturally I have many secondary rigs for different parts, such as accessories, eyes, mouth and other controllers. This addon can save poses for many armatures under one single pose, which you can load for all corresponding armatures at the same time.

### As many libraries as you need
You can create more than one library of poses and name them whatever you want.

### Everything is saved to the Blender file
All your poses and libraries are embeded to the Blender file. This means that you don't have to worry about extra files being generated somewhere on your pc.

### Default armature names
You can further optimize this addon for your workflow by providing a list of the names of the armatures you want to automatically save the poses of. With this, you'll save poses without having to select the armatures, which makes this really convenient and fast to use.

### Quick pose load
Load poses without having to select the armatures. Pressing the Load button will work regardless of your current selection.

Use Guide
=========
Install the addon as usual. After installing, you'll see a text field in the addon's preferences section -in the Blender Preferences / Addons window). If you're like me and always use the same armature names, you can type those there, using commas to separate them, and the addon will automatically save the poses from the armatures with those names. This behavior gets overriden when you do select an armature and enter pose mode -you can even enter pose mode on multiple selected armatures; when doing this, you'll save the pose from those armatures, and not the default ones you'll define in this field.

![](https://i.imgur.com/HPIvAlI.png)

### Save a pose
You'll find this addon in the **Amarillo** drawer in the N-Panel. First, create a Library by clicking on the "+" icon. You can even change the name later.

![](https://i.imgur.com/kd9T3y6.png) ![](https://i.imgur.com/9c3qtmx.png)

To save a pose, enter pose mode on the desired armatures. You don't need to select any bones as the addon will save the transforms of every bone. Press the Save Pose button, give it a name and hit OK.

![](https://i.imgur.com/5yzZXk7.png) ![](https://i.imgur.com/5dhyoMh.png) ![](https://i.imgur.com/9bV8Mbo.png)

That's it. Your pose is saved to the .blend file.

### Load a pose
To load a pose, you don't need to enter pose mode, or even have the armature(s) selected. You have to select the pose you want to load from the list of saved poses, then press Load Selected Pose. Alternatively, you can also just click on the down pointing arrow to the right of every pose in the list.

### Update a pose
If you want to update an existing pose, select it and then press "Save Pose". This will open the saving prompt with the name of the pose you have selected (which is the one you want to update). Just hit OK and that pose will be updated. Keep in mind that poses will be overwritten if you try creating a new pose with the name of a pose that already exists. Be mindful of the names you use.

How this addon was made
=======================
I am actually not very good with python. I made this addon by sitting for a couple hours with ChatGPT and whipping it with my requests and corrections. Make of that what you will 🤖.
