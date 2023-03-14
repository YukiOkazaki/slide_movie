const folderId = "";
let properties = PropertiesService.getScriptProperties();


function getAllSlide(folderId) {
  let folder = DriveApp.getFolderById(folderId);

  const fileType = "application/vnd.google-apps.presentation";
  let files = folder.getFilesByType(fileType);

  let fileArray = [];
  while (files.hasNext()) {
    let file = files.next();
    fileArray.push({ name: file.getName().replace(/[0-9]{6}_/, ""), id: file.getId() });
  }

  return fileArray;
}

function downloadSlide(folder, name, presentationId, slideId) {
  let url = 'https://docs.google.com/presentation/d/' + presentationId + '/export/jpeg?id=' + presentationId + '&pageid=' + slideId;
  let options = {
    headers: {
      Authorization: 'Bearer ' + ScriptApp.getOAuthToken()
    }
  };
  let response = UrlFetchApp.fetch(url, options);
  let image = response.getAs(MimeType.JPEG);
  image.setName(name);
  folder.createFile(image);
}

function saveScenarioSlideImages(presentationName, presentationId, slideFolder) {
  let presentation = SlidesApp.openById(presentationId);
  let scenario = [];
  let folder = slideFolder.createFolder(presentationName);
  presentation.getSlides().forEach(function (slide, i) {
    let pageName = Utilities.formatString('%03d', i + 1) + '.jpeg';
    let txt = '';
    txt += slide.getNotesPage().getSpeakerNotesShape().getText().asString();

    let note = '';
    txt.split('\n').map(function (t) { return t.trim() }).forEach(function (v) {
      note += v;
    });

    scenario.push(note);
    downloadSlide(folder, pageName, presentation.getId(), slide.getObjectId());
  });
  folder.createFile(presentationName + '-scenario.txt', scenario.join('\n'));
}

function saveSlide() {
  let startTime = new Date();
  let slideFolderKey = "slideFolderId";
  let slideKey = "nowSlide";
  let triggerKey = "trigger";

  let folder = DriveApp.getFolderById(folderId);

  let today = Utilities.formatDate(new Date(), 'JST', 'yyMMdd');
  let slideFolderId = properties.getProperty(slideFolderKey);
  let slideFolder;
  if (!slideFolderId) {
    slideFolder = folder.createFolder(`ScenarioSlideImage_${today}`);
    slideFolderId = slideFolder.getId();
  } else {
    slideFolder = DriveApp.getFolderById(slideFolderId);
  }

  let fileArray = getAllSlide(folderId);
  fileArray.sort((m, next_m) => {
    return m.name < next_m.name ? -1 : 1
  })
  console.log(fileArray);

  let nowSlide = parseInt(properties.getProperty(slideKey));
  if (!nowSlide) nowSlide = 0;  // 初回処理の時

  for (let i = nowSlide; i < fileArray.length; i++) {
    // 開始時刻（startTime）と現時点の処理時点の時間を比較する 
    let diff = parseInt((new Date() - startTime) / (1000 * 60));
    if (diff >= 3) {
      // トリガー(3分後)を登録する
      properties.setProperty(slideFolderKey, slideFolderId);
      properties.setProperty(slideKey, i);
      setTrigger(triggerKey, "saveSlide");
      return;
    }

    file = fileArray[i];
    saveScenarioSlideImages(file.name, file.id, slideFolder);
    console.log(`${file.name} is done`);
  }

  // 全て実行終えたらトリガー不要なためを削除する
  deleteTrigger(triggerKey);
}

// 指定したkeyに保存されているトリガーIDを使って、トリガーを削除する
function deleteTrigger(triggerKey) {
  let triggerId = properties.getProperty(triggerKey);
  if (!triggerId) return;

  ScriptApp.getProjectTriggers().filter(function (trigger) {
    return trigger.getUniqueId() == triggerId;
  })
    .forEach(function (trigger) {
      ScriptApp.deleteTrigger(trigger);
    });
  properties.deleteProperty(triggerKey);
}

// トリガーを発行する
function setTrigger(triggerKey, funcName) {
  // 既に同名で保存しているトリガーがあったら削除
  deleteTrigger(triggerKey);

  // トリガーを登録する
  let date = new Date();
  date.setMinutes(date.getMinutes() + 3);
  let triggerId = ScriptApp.newTrigger(funcName).timeBased().at(date).create().getUniqueId();
  Logger.log('setTrigger function_name "%s".', funcName);

  // トリガーを削除するために「スクリプトのプロパティ」にトリガーIDを保存しておく
  properties.setProperty(triggerKey, triggerId);
}

