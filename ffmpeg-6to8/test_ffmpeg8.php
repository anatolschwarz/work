<?php
/*****************************
	Change log: 
	
	2025-04-21 - fixed the sessionName creation on convert flow
	2025-06-08 - supports '-2' flv, by switching to flv '-1'
	2025-06-11 -
		1. 'doKdl' - 
			returns null on non existent flv.
			does not deal with flv '-2'/'-1' switching
		2. 'kdl' option changes - 
			'1' - on flv:-2, switch to -1
			'2' - on non existing flv, switch to 'flvPrmOut' cmdline (non 'kdl' mode
 */
 
/*****************************
 * Includes & Globals
 */
ini_set("memory_limit","512M");
//require_once("/opt/kaltura/app/batch/bootstrap.php");
require_once "/opt/kaltura/app/alpha/scripts/bootstrap.php";
/**/
        // for DEV srvs
if(file_exists("/opt/kaltura/app/tests/lib/KalturaTypes.php"))
        require_once "/opt/kaltura/app/tests/lib/KalturaTypes.php";
else // for the rest ...
        require_once "/opt/kaltura/app/batch/client/KalturaTypes.php";

require_once "KFFMpegMediaParser.php";

/*
require_once "KDLCommon.php";
*/
require_once "KDLFlavor.php";
/*
require_once "KDLOperatorFfmpeg2_1_3.php";
require_once "KDLOperatorFfmpeg2_2.php";
require_once "KDLOperatorFfmpeg2_7_2.php";
require_once "KDLOperatorFfmpeg6_0.php";
require_once "KDLTranscoderCommand.php";
require_once "KDLWrap.php";
*/

require_once "KChunkedEncodeUtils.php";
/*
require_once "KFFmpegFilterGraphHelper.php";
require_once "KFFmpeg6MigrationHelper.php";
require_once "KChunkedEncode.php";

require_once "KBaseChunkedEncodeSessionManager.php";
//require_once "KChunkedEncodeSessionManagerStandalone.php";
require_once "KChunkedEncodeSessionManager.php";
//require_once "KChunkedEncodeDistrExecInterface.php";
require_once "KChunkedEncodeMemcacheWrap.php";
//require_once "KSrtTextHelper.php";
*/
/**/
include_once('KDLTestBenchUtils.php');
include_once('KMediaQualityMeasurementUtils.php');
include_once('KMediaQualityMeasurement.php');

$TEST_CE_AS_LIB=1;
	require_once("test_ce.php");
$TEST_COMPARE_AS_LIB=1;
	require_once("test_kdl_compare.php");

///////////////////////////////////////////////////////////////////////////////
// VMAF checks 
//
	class testAppParamsTestCEJunk extends testAppParamsTestCE {
		public function __construct() {
			$this->concurrent=40;
			$this->minConcurrent=40;
			$this->token="tokenprodng";
			$this->ffmpegBin="ffmpeg";
			$this->ffprobeBin="ffprobe";
		}
		public $action = array("full",
					"convert","compare","compareRenditions");
		public $line = null;
		public $outputFolder = "/web/content/shared/tmp/qualityTest/TestBench.11/ffm8tests";
		public $source = null;
		public $kdl = null;
		public $sessionPrefix= null;
		public $sessionPostfix= null;
		public $kconf=null;
		public $usage = array("ZZZZZZ", );
	}
	
	class testAppParamsCompareForNewFFMpegTesting extends testCompareAppParamsData {
		public function __construct() {
			parent::__construct();
			$this->vmafModelPath = "model/vmaf_v0.6.1.json";
			$this->concurrent=40;
			$this->token="tokenprodng";
			$this->ffmpegBin="ffmpeg";
			$this->ffprobeBin="ffprobe";
			$this->sessionName="";
		}
		public $action = "compare";
		public $line = null;
		public $outputFolder = "/web/content/shared/tmp/qualityTest/TestBench.11/ffm8tests";
		public $usage = array("", );
	}

	/********************
	 *
	 */
	function extractCpuFromLog($logFile) {
		if (!file_exists($logFile)) {
			KalturaLog::log("Log file not found: $logFile");
			return null;
		}
		
		// Read the file content
		$content = file_get_contents($logFile);
		
		// Use regex to find the line and extract CPU value
		if (preg_match('/RESULT:Success!.*cpu:(\d+\.?\d*)/', $content, $matches)) {
			return floatval($matches[1]);
		}
		
		return null;
	}
	
	///////////////////////////////////////////////////////////////////////////////
	/********************
	 *
	 */
	function process($setup, $sessionVals)
	{
		$sessionName = "";
		if(isset($setup->sessionName)){
			$sessionName = $setup->sessionName;
		}
		if(isset($sessionVals->entryId)) {
			KalturaLog::log("ent:$sessionVals->entryId, src:$sessionVals->srcId, par:$sessionVals->partnerId, upd:$sessionVals->updated_at, ast:$sessionVals->assetId, dur:$sessionVals->dur");
			KalturaLog::log("srcPath:$sessionVals->srcPath, astPath:$sessionVals->assetPath");
			if(isset($sessionVals->partnerId)) {
				$partnerToMatch=$sessionVals->partnerId;
			}
			if(!isset($sessionName) || strlen($sessionName)==0)
				$sessionName = $sessionVals->entryId."_$sessionVals->assetId";
		}
		else {
			KalturaLog::log("srcPath:$setup->source, file:$setup->file, file2:$setup->file2");
			if(isset($setup->partner)) {
				$partnerToMatch=$setup->partner;
			}
		}
		
		if(isset($partnerToMatch)) {
			KFFmpegToPartnerMatch::getVersion();
			KFFmpegToPartnerMatch::match($partnerToMatch);
		}
		KFFmpegToPartnerMatch::getVersion();

		if(isset($setup->sessionPrefix) && strlen($setup->sessionPrefix)>0)
			$sessionName = "$setup->sessionPrefix"."_$sessionName";
		if(isset($setup->sessionPostfix) && strlen($setup->sessionPostfix)>0)
			$sessionName = "${sessionName}_$setup->sessionPostfix";
KalturaLog::log("sessionName:$sessionName,$setup->sessionPrefix,$setup->sessionPostfix");
//die;
		$outputPath = "$setup->outputFolder/$sessionName";
		$userCpuArr = null;

		switch($setup->action){
		case "test":
$assetStats = extractAssetExecutionStats($sessionVals->assetPath.".conv.log"); //
if(isset($assetStats->userCpu))
	$assetUserCpu = $assetStats->userCpu;
else $assetUserCpu=null;
			$outputFiles = array("${outputPath}_ff4", "${outputPath}_ff6");
			runTest($setup, $sessionName, $sessionVals, $outputFiles, $assetUserCpu);
			break;
		case "full":
			if(runConvert($setup, $sessionName, $sessionVals, $outputPath, $userCpu)!==true) {
				break;
			}
			$userCpuArr[1] = $userCpu;
		case "convert":
			runConvert($setup, $sessionName, $sessionVals, $outputPath);
			break;
		case "compare":
			$compareFiles = array($sessionVals->assetPath, $outputPath);
			$assetStats = extractAssetExecutionStats($sessionVals->assetPath.".conv.log"); //
			if(isset($assetStats->userCpu))
				$userCpuArr[0] = $assetStats->userCpu;
			runCompare($setup,$sessionName, $sessionVals, $compareFiles, $userCpuArr);
			break;
		case "compareRenditions":
			$rend1UserCpu= extractCpuFromLog($setup->file.".conv.log");
			if(!isset($rend1UserCpu)){
				$assetStats = extractAssetExecutionStats($setup->file.".conv.log"); //
				if(isset($assetStats->userCpu))
					$rend1UserCpu = $assetStats->userCpu;
			}
			$rend2UserCpu= extractCpuFromLog($setup->file2.".conv.log");
			if(isset($rend1UserCpu) && isset($rend2UserCpu)) {
				$userCpuArr[0] = $rend1UserCpu;
				$userCpuArr[1] = $rend2UserCpu;
			}

KalturaLog::log("rendUserCpu:".print_r($userCpuArr,1));
			$compareFiles = array($rend1UserCpu, $rend2UserCpu);
// php test_ffmpeg7.dev.php -action compareRenditions -line "${line}" -sessionPrefix "${PREFIX}" -outputFolder "$COMPARE_FOLDER" -source "${sourcePath}" -file "${assetPath}" -file2 "${rendition}"
			runCompare($setup,$sessionName, null,$compareFiles, $userCpuArr);
			break;
		}
	}
	
	/********************
	 *
	 */
	function parseLine($line)
	{
		$line = str_replace(array('//','/web'),array('/','/nvp1-kalt-ovp-content'),$line);
		$lineVals = explode('~',$line);
		KalturaLog::log(print_r($lineVals,1));
		return $lineVals;
	}
	
	/********************
	 *
	 */
	function runConvert($params, $sessionName, $sessionVals, $outputPath, &$userCpu=null)
	{
//die;
		$srcPath  = $sessionVals->srcPath;
		$cmdLines = $sessionVals->cmdLines;

		if($cmdLines=="NULL"){
			KalturaLog::log("RESULT:Failure, missing cmdLines!!! session:$sessionName");
			return false;
		}
			// cmdLines fixes can be done only after the unserializing
		$cmdLines = unserialize($cmdLines);
		$engine=array_keys($cmdLines)[0];
		switch($engine) {
		case conversionEngineType::CHUNKED_FFMPEG:
			$params->cmd = $cmdLines[$engine];
			break;
//$engine=2;
		case conversionEngineType::FFMPEG:
		case conversionEngineType::CHUNKED_FFMPEG_AUX:
			$srcPath = '"'.kFile::realPath($srcPath).'"';
			$params->cmd = null;
			kBatchUtils::addReconnectParams('"http', $srcPath, $params->cmd);
			$params->cmd = "$params->ffmpegBin ".$params->cmd.$cmdLines[$engine];
			break;
		default:
			KalturaLog::log("RESULT:Failure, bad engine!!! session:$sessionName, engine:$engine");
			return false;
		}
		if(strstr($params->cmd,';;;FS')!==null)
			$doQtFastatart = true;
		
		$params->cmd = str_replace(array(';;;FS','__inFileName__','__outFileName__','__binaryName__'),
								array('',$srcPath,$outputPath,$params->ffmpegBin),$params->cmd);
		$params->cmd = str_replace(array('__waterMarkFileName___1','__waterMarkWidth___1','__waterMarkHeight___1'),
								array('/web/content/shared/tmp/convert_1_l568snmq_bc8bf_1.wmtmp.png',150,150),$params->cmd);
		$params->cmd = str_replace(array('__waterMarkFileName___2','__waterMarkWidth___2','__waterMarkHeight___2'),
								array('/web/content/shared/tmp/convert_1_l568snmq_bc8bf_2.wmtmp.png',150,150),$params->cmd);

		KalturaLog::log("engine $engine:".$params->cmd);
		if($engine==conversionEngineType::CHUNKED_FFMPEG) {
			$rv=simulateAsyncConvert($params->sessionName, $params);
			if(isset($params->stats)){
				$userCpu = $params->stats->userCpu;
				unset($params->stats);
			}
		}
		else {
			$rUsedStart = getrusage(1);
			$lastLine = exec("time $params->cmd", $outputArr, $rv);
            $rUsedEnd = getrusage(1);
			$userCpu = round(($rUsedEnd['ru_utime.tv_sec'] + floatval($rUsedEnd['ru_utime.tv_usec'] / 1000000))
				- ($rUsedStart['ru_utime.tv_sec'] + floatval($rUsedStart['ru_utime.tv_usec'] / 1000000)));

			$rv = ($rv==0)?true:false;
		}
		if($rv!=true) {
			KalturaLog::log("RESULT:Failure!!! session:$sessionName, engine:$engine");
			return $rv;		
		}

		if($doQtFastatart===true) {
			exec("qt-faststart $outputPath ${outputPath}.mp4", $outputArr, $rv);
			if($rv!=0) {
				KalturaLog::log("RESULT:Failure, on qt-faststart!!! session:$sessionName, engine:$engine");
				return false;		
			}
			$outputPath.= ".mp4";
		}
		KalturaLog::log("RESULT:Success!!! session:$sessionName, engine:$engine, outPath:$outputPath, cpu:$userCpu");

		return true;		
	}

	/********************
	 *
	 */
	function extractAssetExecutionStats($logFilename)
	{
KalturaLog::log(print_r($logFilename,1));
		stream_wrapper_restore('http');
		stream_wrapper_restore('https');

/**/		
			if(kFile::checkFileExists($logFilename)==false) {
				KalturaLog::log("Missing log file ($logFilename)");
				return null;
			}

			$logRealFilename = kFile::realPath($logFilename);
			$pattern = KChunkedEncodeSessionManager::SessionStatsJSONLogPrefix;
			$cmdLine = "wget -O- -q '$logRealFilename' | grep -oP '$pattern\K.*'";
			KalturaLog::log($cmdLine);
			$jsonStr = trim(shell_exec($cmdLine));
			$stats=json_decode($jsonStr);

KalturaLog::log(print_r($stats,1));
		stream_wrapper_unregister('https');
		stream_wrapper_unregister('http');
		
		return $stats;
	}

	/********************
	 *
	 */
	function runCompare($setup, $sessionName, $sessionVals, $compareFiles, $userCpu=null)
	{
KalturaLog::log("setup:".print_r($setup,1));
KalturaLog::log("sessionVals:".print_r($sessionVals,1));
//KalturaLog::log("compareFiles:".print_r($compareFiles,1));
//die;
		$compareSetup = clone $setup;
		if(isset($sessionVals)) {
			$compareSetup->source = $sessionVals->srcPath;
			{
				$compareSetup->file = $sessionVals->assetPath;
				$compareSetup->file2 = "$setup->outputFolder/$sessionName";
			}
		}
//		else {
//			$srcPath = $setup->source;
//		}
//$params->vmaf = 0;

		$userCpu2 = null;
		if(isset($userCpu)) {
			if(is_array($userCpu)) {
				$userCpu2 = $userCpu[1];
				$userCpu1  = $userCpu[0];
			}
		}
		if(strstr($compareSetup->cmd,'-vn')!==false)
			$compareSetup->vmaf = 0;
		setVmafBins($compareSetup);
	
#		if(isset($srcPath)) 
		{
//			$compareSetup->source = $srcPath;
//			$compareSetup->file = $comparePath;
//			$compareSetup->file2 = $comparePath2;
//KalturaLog::log(print_r($compareSetup,1));
//$compareSetup->vmaf = 0;
			$rvStr = compareFiles($compareSetup->file, $compareSetup->file2, 
				$compareSetup->source, $compareSetup->source, $compareSetup);
			if(!isset($rvStr) || strstr($rvStr,'RESULT:OK')!==false)
				$rv = true;
			else $rv = false;

		}
/*		else {

			$compareSetup->source = $comparePath;
			$compareSetup->file = $comparePath2;
			$compareRv = compareFileToSource($compareSetup->file, $compareSetup->source, $compareSetup);
			if(isset($compareRv->analysis["compareObjects"])) {
				$rv = false;			
				$rvStr = $compareRv->analysis["compareObjects"];
			}
			else 
				$rv = true;

		}
*/
		$cpuStr = compareUserCpu($userCpu1, $userCpu2);
		if($rv==true) {
			$rvStr = "RESULT:Success!!! session:$sessionName;anlys:$rvStr;$cpuStr";
		}
		else 
			$rvStr = "RESULT:Failure!!!session: $sessionName;anlys:$rvStr;$cpuStr";
		KalturaLog::log($rvStr);
		return $rvStr;
	}

	/********************
	 *
	 */
	function compareUserCpu($userCpu1, $userCpu2, $eqTrshRat=0.98, $lrgTrshRat=1.1, $minTrsh=30)
	{
		$cpuStr=null;
		if(isset($userCpu1) && isset($userCpu2) && $userCpu2!=0){
			$ratio = round($userCpu1/$userCpu2,3);
			if(abs(1-$ratio)<(1-$eqTrshRat)) {
				$cpuStr = "eq";
			}
			else if($ratio>1){
				$cpuStr = "2nd";
			}
			else {
				$cpuStr = "1st";
				$ratio = round(1/$ratio,3);
			}

			KalturaLog::log("cpu1:$userCpu1, cpu2:$userCpu2, trsh:(eq:$eqTrshRat,lrg:$lrgTrshRat,min:$minTrsh) ==> ratio:$ratio");
			if($ratio>$lrgTrshRat && $userCpu1>$minTrsh && $userCpu2>$minTrsh){
				$cpuStr.= '+';
			}
			
			$cpuStr = "CPU:$cpuStr,$userCpu1,$userCpu2";
		}
		else if(isset($userCpu1)){
			$cpuStr = "CPU:NA,$userCpu1,na";
		}
		else if(isset($userCpu2)){
			$cpuStr = "CPU:NA,na,$userCpu2";
		}
		return $cpuStr;
	}
	
	/********************
	 *
	 */
	function runTest($params, $sessionName, $sessionVals, $outputFiles,$userCpu3=null)
	{
		$srcPath  = $sessionVals->srcPath;
		$cmdLines = $sessionVals->cmdLines;
		
		$paramsAux = clone $params;
		$paramsAux->ffmpegBin = "ffmpeg";
		$paramsAux->ffprobeBin = "ffprobe";
		
		$outputPath=$outputFiles[0];
		$outputPath2=$outputFiles[1];
		
		if(runConvert($paramsAux, $sessionName, $sessionVals, $outputPath, $userCpu)!==true)
			return;
//$userCpu = 154.22;
		$userCpuArr[0] = $userCpu;

		if(runConvert($params, $sessionName, $sessionVals, $outputPath2, $userCpu)!==true)
			return;
//$userCpu = 173.23;
		$userCpuArr[1] = $userCpu;
		
		$compareFiles = array($outputPath, $outputPath2);
		$rvStr = runCompare($params,$sessionName, $sessionVals, $compareFiles, $userCpuArr);
		if(isset($userCpu3)){
			$cpuStr = compareUserCpu($userCpu3, $userCpuArr[1]);
			$rvStr.= ";ast:$cpuStr";
		}
		KalturaLog::log($rvStr);
	}
	
	/********************
	 *
	 */
	function doKdl($sessionVals, $flavorId=null)
	{
		$sourceId=$sessionVals->srcId;
		$assetId=$sessionVals->assetId;
KalturaLog::log("soutce:$sourceId, asset:$assetId, flavorId:$flavorId");
		$mediaInfo = mediaInfoPeer::retrieveOriginalByEntryId($sessionVals->entryId);
		if(!isset($mediaInfo))
			$mediaInfo = mediaInfoPeer::retrieveByFlavorAssetId($sourceId);
		if(!isset($mediaInfo))
			$mediaInfo = getMediaInfo($sessionVals->srcPath);
		$asset = assetPeer::retrieveById($assetId);
		
		if(isset($flavorId))
			;
		else if(isset($asset)){
			$flavorId=$asset->getFlavorParamsId();
		}
		else $flavorId=487061;

KalturaLog::log("flavorId:$flavorId");
$medSet=new KDLMediaDataSet;
KDLWrap::ConvertMediainfoCdl2Mediadataset($mediaInfo, $medSet);
		$flavorObj=assetParamsPeer::retrieveByPK($flavorId);
		if(!isset($flavorObj)) {
			KalturaLog::log("ERROR: Failed to extract flavor params $flavorId. Exiting!");
			return null; 
		}
KalturaLog::log(print_r($flavorObj,1));
KalturaLog::log("chk $flavorId:".$flavorObj->getChunkedEncodeMode());

		$flavorArr[] = $flavorObj;
		$targets = KDLWrap::CDLGenerateTargetFlavors($mediaInfo, $flavorArr);
		$cmdLines = $targets->_targetList[0]->getCommandLines();
		KalturaLog::log(print_r($cmdLines,1));
		KalturaLog::log(print_r($targets,1));
		return serialize($cmdLines);
 /**/
	}

	/********************
	 *
	 */
	function getMediaInfo($sourceFile)
	{
			$medPrsr = new KFFMpegMediaParser($sourceFile);
			$m1=$medPrsr->getMediaInfo();
KalturaLog::log(print_r($m1,1));
			$m2=new mediaInfo;

			$parsedArgsArr = get_object_vars($m1);
			foreach ($parsedArgsArr as $nm=>$val){
					$funcNm="set".ucfirst($nm);
					if(method_exists($m2, $funcNm))
							$m2->$funcNm($val);
					else
							KalturaLog::log("No func:$funcNm, val:$val");
			}
			return $m2;
	}

///////////////////////////////////////////////////////////////////////////////
	/********************
	 *
	 */
	function main($argv)
	{
		print_r(gethostname()."\n");
		$tm = microtime(true);
		print_r($tm."\n");

		$setup = new testAppParamsTestCEJunk();
		$setup = testAppParams::parseArgs($argv,$setup);
KalturaLog::log(print_r($setup,1));
//die;
/*
KalturaLog::log("ZZZ - ".print_r($setup,1));
$medPrsr = new KFFMpegMediaParser($setup->source, $setup->ffmpegBin, $setup->ffprobeBin);
$m=$medPrsr->getMediaInfo();
KalturaLog::log(print_r($m,1));
die;
*/


		if(isset($setup->kconf)){
			
#KFFmpegToPartnerMatch::$kConfEmulateFilename="http://ny-www.kaltura.com/content/shared/tmp/emulateKConf.txt";
			if(strstr($setup->kconf,'http')!==false) {
				$tmpName='emulateKConf_'.uniqid();
				$tmpName=kFile::getExternalFile($setup->kconf,'/tmp',$tmpName);
				KFFmpegToPartnerMatch::$kConfEmulateFilename = $tmpName;
			}
			else
				KFFmpegToPartnerMatch::$kConfEmulateFilename = $setup->kconf;
		}
KalturaLog::log(print_r(KFFmpegToPartnerMatch::$kConfEmulateFilename,1));
//die;
		switch($setup->action){
		case "test":
		case "full":
			$setup = new testAppParamsTestCEJunk();
			$aux = new testAppParamsCompareForNewFFMpegTesting();
			$setup->vmaf = $aux->vmaf;
			$setup->vmafSubsample = $aux->vmafSubsample;
			$setup->samplesCount = $aux->samplesCount;
			$setup->duration = $aux->duration;
			$setup = testAppParams::parseArgs($argv,$setup);
			break;
		case "convert":
			$setup = new testAppParamsTestCEJunk();
			$setup = testAppParams::parseArgs($argv,$setup);
			break;
		case "compare":
		case "compareRenditions":
			$setup = new testAppParamsCompareForNewFFMpegTesting();
			$setup->kdl="";
			$setup->sessionPrefix="";
			$setup->sessionPostfix="";
			$setup = testAppParams::parseArgs($argv,$setup);
			if(!isset($setup->samplesCount) || $setup->samplesCount==0){
				$setup->duration=30;
			}
			break;
		}
		if(count($argv)<4) {
			KalturaLog::log(print_r($setup,1));
			exit;
		}

		KalturaLog::log(print_r($setup,1));

		if(isset($setup->shared) && $setup->shared!=0)
			$setup->shared = '/nvp1-kalt-ovp-apptemp/convert/chunked/';
		else
			$setup->shared = null;
		$sessionVals = new stdClass;
		if(isset($setup->line) && strlen($setup->line)>0) {
			$stam=0;
			list($sessionVals->entryId,$sessionVals->srcId, $sessionVals->partnerId, $sessionVals->updated_at,
				$sessionVals->srcPath, $sessionVals->assetId, $sessionVals->assetPath,
				$sessionVals->cmdLines, $sessionVals->dur,
				$stam,$stam,$stam,$sessionVals->flavor) = parseLine($setup->line);
		}
		if(isset($setup->partner)) {
			$sessionVals->partnerId=$setup->partner;
		}
KalturaLog::log("setupPart:".$setup->partner."\n".print_r($sessionVals,1));
		if($setup->kdl==1){
			if($sessionVals->flavor==-2)
				$cmdLines=doKdl($sessionVals,-1);		
			else 
				$cmdLines=doKdl($sessionVals);
			KalturaLog::log(print_r($cmdLines,1));
			$sessionVals->cmdLines=$cmdLines;
		}
		else if($setup->kdl==2){
			$cmdLines=doKdl($sessionVals);
			if(isset($cmdLines)) {
				KalturaLog::log(print_r($cmdLines,1));
				$sessionVals->cmdLines=$cmdLines;
			}
		}

		KalturaLog::log(print_r($sessionVals,1));
		process($setup, $sessionVals);
	}

	/********************
	 *
	 */
	KalturaLog::log(gethostname());
$map = kconf::get('ffmpeg', 'runtime_config', array());
KalturaLog::log(print_r($map,1));
//die;
	main($argv);
	die;
