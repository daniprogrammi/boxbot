# boxbot

Twitch bot for my stream -- enabling user participation and a pleasant level of chaos

## Admin Commands

---
`New <user>` - Add new user to database.

`user_list` - Get a list of users.

`obsinit` - Initialize OBS.

`obsversion` - Current version of OBS.

`getItems` - Get Scene Items

`set_visible {sceneItemName} {Item}` - Set scene item to be visible.

`curscene` - Get the current scene from obs.

`enabled {sceneItemname}` - Check if scene is enabled or not.

`inputlist {requestName}` - Get input List.

`setInputSettings {requestName}` - Set input settings.

`getOutput {outputName}` - Get settings.

`setOutput {outputName} {outputSetting} {outputSettingvalue}` - Set Output values.

`getMediaStatus {mediaName}` - Get media Input Status.

`media {source} {action}` Set a media source with an action.

`toggle {sourceName}` - Toggle a source.

## User Commands

`vlc_link` - Add a link to the queue.

- Example: `!vlc_link https://www.youtube.com/watch?v=0NsK-U8dyDE`

`play` - Play next item in the queue.

- Example: `!play`

`playing` - Get the current playing link.

- Example: `Playing "stop the cap!" - Youtube`

`queue` - Get the number of items in the queue.

- Example: `Currently in queue: 5`

`box` - Dig in the box for an asset.

- Example: `!box videos`, will play a video from the box.

- Choices: `audio`, `images`, `videos`, `gifs`, `text`

`lurk` - Lurk into the safety of the box.

`so` - Shoutout someone cool or maybe not so cool.

`welcome` - Welcome in the raid party with a nice message.

`sub` - Message from Dani on the thoughts of giving subs.

`hrc` - Link to Human Rights compaign for trans & non-binary peoples.

`aapi` - Link to resources to help stop anti-Asian violence.

`blm` - Link to resource, info, & donation to support Black Lives matter.

`tiktok` - Link to GirlWithBox Tik tok account.

`abortions` - Link to donate to abortion funds.

`project` - Get the Current project that I'm working on!

`discord` - Link to my beautiful discord that I barely maintain.

`twitter` - Link to the nastiness of a social media called twitter.

`github` - Link to my github that you may or may not see me use.
