# Page 1

Meta-Harness: End-to-End Optimization of Model Harnesses
YoonhoLee RoshenNair QizhengZhang KangwookLee
Stanford Stanford Stanford KRAFTON
OmarKhattab ChelseaFinn
MIT Stanford
Projectpagew/interactivedemo:https://yoonholee.com/meta-harness/
Optimizedharness:https://github.com/stanford-iris-lab/meta-harness-tbench2-artifact
55
50
45
40
35
30
0 10 20 30 40
Harness Evaluations
)%(
ecnamrofreP
tseB
Harness Optimizer Search Progress
Meta-Harness
40
TTT-Discover 35 OpenEvolve
ACE 30
Few-shot
Zero-shot 25
20
)%(
etaR
ssaP
TerminalBench-2 Harness Performance
Human-written
Meta-Harness (ours) Model-optimized (ours)
37.6 Goose
35.5 Terminus-KIRA
33.7 Mini-SWE- Agent
29.8 Terminus-2 C C la o u d d e e 28.3 27.5
Figure 1: (Left) On text classification, Meta-Harness outperforms the best prior hand-
designedharnesses(ACE)andexistingtextoptimizers(TTT-Discover,OpenEvolve),match-
ingthenext-bestmethod’sfinalaccuracyafterjust4evaluations. (Right)OnTerminalBench-
2,Meta-HarnessoutperformsallreportedClaude Haiku 4.5harnesses.
Abstract
The performance of large language model (LLM) systems depends not
onlyonmodelweights,butalsoontheirharness: thecodethatdetermines
whatinformationtostore,retrieve,andpresenttothemodel. Yetharnesses
arestilldesignedlargelybyhand,andexistingtextoptimizersarepoorly
matchedtothissettingbecausetheycompressfeedbacktooaggressively:
theyarememoryless,conditiononlyonscalarscores,orrestrictfeedbackto
shorttemplatesorsummaries. WeintroduceMeta-Harness,anouter-loop
systemthatsearchesoverharnesscodeforLLMapplications. Itusesan
agenticproposerthataccessesthesourcecode,scores,andexecutiontraces
ofallpriorcandidatesthroughafilesystem. Ononlinetextclassification,
Meta-Harnessimprovesoverastate-of-the-artcontextmanagementsystem
by7.7pointswhileusing4×fewercontexttokens. Onretrieval-augmented
math reasoning, a single discovered harness improves accuracy on 200
IMO-levelproblemsby4.7pointsonaverageacrossfiveheld-outmodels.
Onagenticcoding,discoveredharnessessurpassthebesthand-engineered
baselines on TerminalBench-2. Together, these results show that richer
accesstopriorexperiencecanenableautomatedharnessengineering.
1 Introduction
Changing the harness around a fixed large language model (LLM) can produce a 6×
performancegaponthesamebenchmark[47]. Theharness—thecodethatdetermineswhat
tostore,retrieve,andshowtothemodel—oftenmattersasmuchasthemodelitself. This
sensitivityhasledtogrowinginterestinharnessengineering,thepracticeofrefiningthe
codearoundanLLMtoimprovetheoverallsystem’sperformance[36;21;10;9]. Butdespite
itsimportance,harnessengineeringremainslargelymanual: practitionersinspectfailures,
1
6202
raM
03
]IA.sc[
1v25082.3062:viXra

Table 1:

TerminalBench-2 Harness Performance
Human-written
Meta-Harness
40 (ours) Model-optimized (ours)
37.6 Goose
)%( 35.5 Terminus-KIRA
35 33.7
etaR Mini-SWE-
Agent
30 ssaP 29.8 Terminus-2 C C la o u d d e e 28.3
27.5
25
20 |  |  |  |  |  |  |  |  |  |  |  |  | 
 | Meta-Harness
(ours) |  |  |  |  |  |  | Human-written
Model-optimized (ours) |  |  |  |  | 
 |  |  |  |  |  |  |  |  |  |  |  |  | 
 | 37.6 Goose
35.5 Terminus-KIRA |  |  |  |  |  |  |  |  |  |  |  | 
 |  |  |  |  |  |  |  |  |  |  |  |  | 
 |  |  |  |  | 33.7
Mini-SWE-
Agent |  |  |  |  |  |  |  | 
 |  |  |  |  |  |  |  |  |  |  |  |  | 
 |  |  |  |  |  |  | 29.8 Terminus-2 C C la o u d d e e
28.3
27.5 |  |  |  |  |  | 
 |  |  |  |  |  |  |  |  |  |  |  |  | 
 |  |  |  |  |  |  |  |  |  |  |  |  | 
 |  |  |  |  |  |  |  |  |  |  |  |  | 
 |  | ss o
s(TT
alua
ku |  | perf
-Dis
ons.
5ha |  | ms
ver,
Righ
esse |  | e be
pen
On |  | pri
olve
rmin |  | han
mat
Ben | 


# Page 2

Filesystem w8 Maximize
Harness Harness+LLM
All Experience Tasks
/
Evaluate
Propose(cid:19)
Harness Code
1 2
Store all Logs to Filesystem
Proposed Reasoning Evag
Code Traces Score
Figure2: Meta-Harnesssearchloop. (1)Anagentreadsafilesystemcontainingallprior
candidates’sourcecode,executiontraces,andscores,andproposesanewharness. (2)We
evaluatetheproposedharnessonevaluationtasks. (3)Alllogs(proposedcode,reasoning
traces,evaluationscores)arestoredinthefilesysteminanewdirectory,andthelooprepeats.
Method History Logcontent MTok/iter
OPRO[51] Window past(solution,score)pairs 0.002
TextGrad[53] Last textualfeedbackoncurrentartifact 0.015
AlphaEvolve[35] Window programdatabase+eval.scores 0.022
GEPA[1] Summary reflectivefeedbackfromrollouttraces 0.008
FeedbackDescent[26] Summary comparison+textualfeedback 0.012
TTT-Discover[54] Window prev.solutionfragment 0.026
Meta-Harness Full alllogsandscores 10.0
Table1: Comparisonoftextoptimizationmethodsandtheirsettings. Eachrowrepresents
amethodcollapsedacrosstasks. Mtok/iterisourbestestimateofthefullcontextgenerated
fromoneevaluationofatextartifactinthelargestsettingconsideredineachpaper. Thispaper
considerssettingsthatyieldorders-of-magnitudemorecontextperartifactevaluation.
adjustheuristics,anditerateonasmallnumberofdesigns. Inthispaper,weaskwhether
thisprocessitselfcanbeautomated.
Anaturalstartingpointisrecentworkontextoptimization,sinceharnessengineeringalso
involvesiterativelyimprovingtextandcodeartifactsusingfeedbackfrompriorattempts[38;
39;35;26;1]. However,thesemethodsarepoorlymatchedtoharnessengineeringbecause
theytypicallyoperatewithshort-horizonorheavilycompressedfeedback: somecondition
onlyonthecurrentcandidate[31;51;53],othersrelyprimarilyonscalarscores[35;12],and
othersrestrictfeedbacktoshorttemplatesorLLM-generatedsummaries[1;26]. Thisisa
pragmaticscalabilitychoice,notevidencethatlonger-rangedependenciesareuninformative.
Harnessesactoverlonghorizons: asinglechoiceaboutwhattostore,whentoretrieveit,or
howtopresentitcanaffectbehaviormanyreasoningstepslater.Compressedfeedbackoften
removestheinformationneededtotracedownstreamfailurestoearlierharnessdecisions.
Acrossthetasksstudiedbyseveralrepresentativetextoptimizers,theavailablecontextper
optimizationsteprangesfromonly100to30,000tokens(Table1),farbelowthediagnostic
footprint of harness search. More broadly, work on retrieval and memory-augmented
languagemodelssuggeststhatusefulcontextshouldoftenbeaccessedadaptivelyrather
thanmonolithicallypackedintoasingleprompt[28;48;37;56].
WeaddressthislimitationwithMeta-Harness,anagenticharnessforoptimizingharnesses
viaend-to-endsearch(Figure2). Itsproposerisacodingagent,i.e.,alanguage-model-based
systemthatcaninvokedevelopertoolsandmodifycode. Thechoiceofcodingagent(rather
thanrawLLM)mattersbecausetheamountofexperiencequicklyexceedscontextlimits,so
theproposermustdecidewhattoinspectandvalidateeditsthroughdirectinteractionwith
thecodebase. Itskeydesignchoiceistoexposefullhistorythroughafilesystem,enabling
selectivediagnosisofrawpriorcodeandexecutiontracesratherthanoptimizationfrom
compressedper-candidatesummaries. Foreverypreviouscandidateharness,thefilesystem
storesthesourcecode,evaluationscores,andexecutiontraces,whichtheproposerretrieves
viastandardoperationssuchasgrepandcatratherthaningestingthemasasingleprompt.
Inpractice,theproposerreadsamedianof82filesperiterationinourmostdemanding
setting, referencing over 20 prior candidates per step (Appendix A). In the settings we
2


# Page 3

study,asingleevaluationcanproduceupto10,000,000tokensofdiagnosticinformation,
roughlythreeordersofmagnitudebeyondthelargestfeedbackbudgetsusedinpriortext
optimizationsettings(Table1).
WeevaluateMeta-Harnessononlinetextclassification,mathematicalreasoning,andagentic
coding. Ononlinetextclassification,harnessesdiscoveredbyMeta-Harnessimproveover
AgenticContextEngineering(ACE,Zhangetal.[59])by7.7pointswhileusing4×fewer
contexttokens,andmatchthenext-besttextoptimizer’sfinalperformanceafter60proposals
with only four (Figure 1). On retrieval-augmented math reasoning, a single discovered
harnessimprovesaccuracyon200IMO-levelproblemsby4.7pointsonaverageacrossfive
held-outmodels. OnTerminalBench-2,thediscoveredharnesssurpassesTerminus-KIRA
andranks#1amongallHaiku4.5agents.
2 RelatedWork
Atahighlevel,Meta-Harnessbringsideasfromthebroaderliteratureoncreditassignment
andmeta-learning[40;46;3;17;44;2]inanewregimeenabledbyrecentadvancesincoding
agents. Rather than updating model weights, the system assigns credit at the harness
level: itusesexperiencefrompastrolloutstodeliberatelyreasonaboutwhichstepsand
componentsareresponsibleforfailures,thenrewritestheexternalcodethatgovernsfuture
behavior. Morespecifically,themethodliesattheintersectionofseveralrecentresearch
threads;itismostdirectlyrelatedtoworkonadaptiveaccesstoexternalcontext,executable
codesearch,andtextoptimization.
Externalmemoryandadaptiveaccess. Severalpriorworksnotethebenefitsoftreating
largeknowledgesourcesorlonginputsasexternalresourcesthatalanguagemodelaccesses
adaptively,ratherthanconsumingtheminasinglepass. Specifically,retrieval-augmented
generation [28], interleaved retrieval and reasoning [48], memory-based agents [37], or
recursive language models [56] are mechanisms for adaptive access to external context.
Meta-Harnessusesasimilaraccesspattern,butinthemoredemandingsettingofharness
engineering,wheretheproposerselectivelyinspectsalargeexternalhistoryofcode,scores,
andexecutiontracestoimprovecontext-managementproceduresthemselves.
Executablecodesearch. Recentmethodssearchoverexecutablecodeforfunctions,work-
flows,oragentdesigns. Earlyworkproposesusinglargemodelsasmutationandcrossover
operatorsinevolutionaryprogramsearch[27]. Latermethodsevolvedesignatedfunctions
withinfixedprogramscaffolds[39],usemeta-agentstoprogramnewagentsfrompriordis-
coveries[20],orsearchoverworkflowgraphsforagenticsystems[58]. Anotherlineofwork
searchesovermemorydesignsforcontinual-learningagents,wherememorypersistsacross
taskstreams[57;50]. Incontrast,Meta-Harnesssearchesoverdomain-specificharnesses,
including prompt construction, retrieval, and state update strategies that reset between
tasks. Itsouterloopisdeliberatelyminimal:insteadofrelyingonafixedscaffold,anarchive
ofpriordiscoveries,orapersistentmemorymechanism,itgivestheproposerunrestricted
filesystemaccesstopriorexperience. Thisletstheagentdecidewhatinformationtoinspect
andenablessearchoverfullharnessimplementationsratherthanapredefinedspaceof
context-managementprocedures.
Text optimization methods. Meta-Harness is also closely related to methods such as
ProTeGi,TextGrad,OPRO,GEPA,AlphaEvolve/OpenEvolve,andFeedbackDescent,which
iterativelyimprovepromptsorothertextartifactsusingfeedbackfrompriorattempts[38;
31;53;51;1;35;43;26]. However,thesemethodsarelesswellsuitedtoharnessengineering,
whereoptimizationtargetsacompleteexecutableprocedure,andtherelevantenvironmental
feedbackisdistributedacrosscode,scores,andexecutiontracesinawaythatishardto
summarize up front. Rather than reacting only to aggregate scores or summaries, the
proposerinMeta-Harnesscanreasonoverfailedexamplesandtheirexecutiontracesto
proposetargetededits. SeeTable1foracomparisonofproblemscaleconsideredinthose
papersandours,andFigures1and4foradirectcomparisonwithOpenEvolve,GEPA,and
TTT-Discoverinourproblemsetting.
3


# Page 4

3 Meta-Harness: AHarnessforOptimizingHarnesses
This section describes Meta-Harness, our outer-loop procedure for searching over task-
specificharnesses. Meta-Harnessisbuiltontheideathatharnessoptimizationbenefitsfrom
allowingaproposertoselectivelyinspectpriorcodeandexecutiontracesviafilesystem
access,ratherthanoptimizingfromlossysummariesoranadditionalhand-designedsearch
structure. Atahighlevel,itrepeatedlyproposes,evaluates,andlogsnewharnesses.
Meta-Harnessisitselfaharnessinthebroadsense(hencethename),sinceitdetermines
whatinformationtheproposermodelseesduringsearch. Unlessotherwisenoted,weuse
harnesstorefertothetask-specificprogramsbeingoptimized.
Objective. Aharnessisastatefulprogramthatwrapsalanguagemodelanddetermines
whatcontextthemodelseesateachstep. Thegoalissimple: findtheharnessthatmakes
theunderlyingmodelperformbestonthetargettaskdistribution. Formally,let Mdenotea
fixedlanguagemodelandX ataskdistribution. Foraharness Handtaskinstancex ∼ X,
weexecutearollouttrajectoryτ ∼ p (H,x). Theharnessconstructspromptsfor M,the
M
modelresponds,andtheharnessupdatesitsstateaftereachinteraction. Atask-specific
rewardfunctionr(τ,x)scoresthetrajectory. Theobjectiveofharnessoptimizationistofind
theharnessthatmaximizestheexpectedfinalreward:
H ∗ =argmaxE r(τ,x),
x∼X,τ∼pM (H,x)
H
Whenmultipleobjectivesarerelevant(e.g.,accuracyandcontextcost),weevaluatecandi-
datesunderParetodominanceandreporttheresultingfrontier. Inpractice,thissearchhas
traditionallybeencarriedoutbyhumanengineersandresearchers,whoiterativelyrefine
prompts,context-managementrules,andtool-uselogicbyhand.
Meta-Harnesssearchloop. Meta-Harnessusesasinglecoding-agentproposerwithaccess
to a growing filesystem D that serves as its feedback channel1. Here, a coding agent is a
language-model-basedsystemthatcaninvokedevelopertoolsandmodifycode. Unlike
priorsystemsthatexternalizetheimprovementlogicinahand-designedsearchloop,Meta-
Harnessdelegatesdiagnosisandproposaltothecodingagentitself: itdecideswhichprior
artifactstoinspect,whichfailuremodestoaddress,andwhethertomakealocaleditora
moresubstantialrewrite.Equivalently,theproposerisnotarawnext-tokenmodeloperating
onafixedpromptassembledbytheouterloop; itisanagentthatretrievesinformation,
navigatespriorartifacts,andeditscodeaspartofthesearchitself. Eachevaluatedharness
contributes a directory containing its source code, scores, and execution traces (such as
prompts,toolcalls,modeloutputs,andstateupdates). Thefilesystemistypicallyfarlarger
thantheproposer’scontextwindow,sotheproposerqueriesitthroughterminaltoolssuch
asgrepandcatratherthaningestingitasasingleprompt. Ateachiteration,theproposer
firstinspectspriorcode,scores,andexecutiontraces,thenreasonsaboutlikelyfailuremodes
beforegeneratinganewharness.
Meta-HarnessmaintainsapopulationHandaParetofrontieroverevaluatedharnesses,but
imposesnoparent-selectionrule: theproposerisfreetoinspectanypriorharnessandits
executiontracewhenproposingnewones. Werunevolutionforafixednumberofiterations
andperformafinaltest-setevaluationontheParetofrontier. Thissimplicityisdeliberate:
by leaving diagnosis and edit decisions to the proposer rather than hard-coding search
heuristics,Meta-Harnesscanimproveautomaticallyascodingagentsbecomemorecapable.
Theproposerneverseestest-setresults;itsonlyfeedbackcomesfromthesearchset,the
subsetoftaskinstancesusedtoevaluatecandidateharnessesduringsearchandgenerate
thefeedbacksignalforimprovement,andfromexecutiontracesloggedduringthosesearch
runs.
Advantagesofcode-spacesearch. Harnessoptimizationoccursincodespace,wheresmall
changestoretrieval,memory,orprompt-constructionlogiccanaffectbehaviormanysteps
later,makinglocalsearchheuristicspoorlymatchedtotheproblem. Byinspectingexecution
1Basedonearlierexploration,wethinkthisworkflowonlybecamepracticalrecently,following
majorimprovementsincoding-agentcapabilitiesaroundearly2026.
4


# Page 5

Algorithm1Meta-Harnessouterloopoverharnesses
1: Input: tasksX,LLM M,proposerP,iterationsN
2: Initialize: populationH ▷Initialsetofvalidharnesses
3: Initialize: filesystemD ← ∅ ▷storescode,scores,traces
4: forH ∈ Hdo
5: E H ←Evaluate(H,M,X)
6: D ← D∪{(H,E H )}
7: fort =1...Ndo
8: ProposerPqueriesfilesystemD ▷inspectspriorharnessesandscores
9: ProposerPproposesknewharnesses{H 1 ,...,H k }
10: forHin{H 1 ,...,H k }do
11: ifHpassesinterfacevalidationthen
12: D ← D∪{(H,EVALUATE(H,M,X))}
13: returnParetofrontierofharnessesstoredinD
traces,theproposercanofteninferwhyaharnessfailedandwhichearlierdesignchoices
likelycontributedtothefailure,notjustthatitfailed,asillustratedbythesearchtrajectories
in Appendices A and A.2. There, we see that the proposer reads broadly across prior
code and logs, then uses those traces to identify confounded edits, isolate likely causal
changes,andshifttowardsafermodificationsafterrepeatedregressions. Theproposercan
thereforemodifytheharnessatthelevelofalgorithmicstructure,rangingfromchanges
toretrieval, memory, orprompt-constructionlogictofullprogramrewrites, ratherthan
fillingintemplatesorapplyingpredefinedmutationoperators. Inpractice,itoftenstarts
from a strong prior harness, but this is an emergent strategy rather than a hard-coded
rule. Althoughthesearchspaceislarge,representingharnessesasprogramsprovidesa
naturalregularizationbias: codingmodelstendtoproposecoherentalgorithmsratherthan
brittle,hard-codedsolutions,whichbiasesthesearchtowardreusablecontext-management
procedures. Thisactionspaceiscloselyalignedwiththeread–write–executeworkflowson
whichfrontiercodingassistantsaretrained.
Practicalimplementation. Inourexperiments,eachharnessisasingle-filePythonprogram
thatmodifiestask-specificprompting,retrieval,memory,andorchestrationlogic. Inour
experiments,theproposerPisClaudeCode[4]withOpus-4.6. Theproposerisguidedbya
minimaldomain-specificskillthatdescribeswheretowritenewharnesses,howtoinspect
previous harnesses and their execution traces, and what files it can and cannot modify.
Thebasemodel Mvariesbydomainandisalwaysfrozen;seeSection4fordetails. Inour
experiments,atypicalrunevaluatesroughly60harnessesover20iterations. Weprovide
additionaltipsforimplementingMeta-HarnessinanewdomaininAppendixD.
4 Experiments
WeevaluateMeta-Harnessonthreetaskdomains: onlinetextclassification,mathreasoning,
andagenticcoding.Ineachdomain,wecompareharnessesdiscoveredbyoursearchagainst
domain-appropriatebaselinesusingthestandardevaluationmetric. Pleaserefertoeach
subsectionforthepreciseexperimentalsetup.
Wecompareagainsttwomainclassesofmethods. (1)Human-designedstrategies: these
are hand-crafted harnesses for each domain, representing the current state of the art in
context construction. We describe these baselines in the corresponding subsections. (2)
Program-searchmethods: thesemethodssearchovercandidateharnessesusingfeedback
andrewardsignals,butaredesignedforsmaller-scalesettingsthanharnessengineering.
4.1 OnlineTextClassification
We follow the online text classification setup of Zhang et al. [59]; Ye et al. [52]: an LLM
receiveslabeledexamplesoneatatime,updatesitsmemory,andisevaluatedonaheld-
outtestset. WeuseGPT-OSS-120BastheLLMtextclassifier,andconsidertheproblemof
5


# Page 6

Datasets Avg.
Harness USPTO S2D Law Acc Ctx↓ 50
Zero-Shot 12.0 63.2 7.0 27.4 0
45
Few-Shot(8) 14.0 67.9 21.0 34.3 2.0
Few-Shot(32) 13.0 72.2 21.0 35.4 7.9 40
Few-Shot(all) 15.0 78.3 29.0 40.8 12.3
35
MCE[52]† 14.0 83.0 23.0 40.0 28.5
ACE[59]† 16.0 77.8 29.0 40.9 50.8 30
Meta-Harness 14.0 86.8 45.0 48.6 11.4 25
0 10k 20k 30k 40k 50k
Table2: Test-setmetricsforallharnessesonthe
threedatasets. Ctxdenotesadditionalinputto-
kensincontext(thousands). †:implementation
from Ye et al. [52]. ↓: lower is better. Meta-
Harnessimprovesonlinetextclassificationac-
curacywhileusingasmallerinputcontext.
ycarucca
tseT
Ours (Pareto)
Ours (non-Pareto)
MCE
ACE
Zero-shot
Few-shot
115k 200k
Additional context (chars)
Figure 3: Pareto frontier of accuracy vs.
context tokens on online text classifica-
tion. Meta-Harness achieves a stronger
accuracy-contextParetofrontierthanall
comparisonmethods.
designingaharnessfortextclassification. Weusethreedatasets,chosenfordifficultyand
domaindiversity: LawBench(Law)[16]predictscriminalchargesfromcasedescriptions
(215classes);Symptom2Disease(S2D)[19]predictsdiseasesfromsymptomdescriptions
(22 classes); and USPTO-50k [41] predicts precursor reactants from product molecules
(180classes). Weinitializethesearchpopulation H fromthemainbaselineharnessesin
thissetting: zero-shot,few-shot,ACE,andMCE.Weran20evolutioniterationswithtwo
candidatesperiteration,producing40candidateharnesses.
Comparisonvstextoptimizers. WecompareMeta-Harnessagainstrepresentativemethods
foroptimizingtext.Forafaircomparison,weusethesameproposerconfiguration(Opus-4.6
withmaxreasoning),selectcandidatessolelybasedonsearch-setperformance,andholdout
thetestsetsuntilthefinalevaluation. Sinceevaluationisthemaincomputationalbottleneck,
wegiveeachmethodthesamebudgetofproposalharnessevaluations. Weconsiderthe
followingpointsofcomparison:
• Best-of-N: independent samples from the seed with no search structure; a compute-
matchedcontrolforwhethersearchmattersatall.
• OpenEvolve[43]: evolutionarysearchoverprogramswithLLMmutation.
• TTT-Discover[55]: weuseonlythetext-optimizationcomponentoftheirmethod,i.e.,
proposalselectionviathePUCTreuserule.
Inthissetting,Meta-Harnessmatchesthebestpriortextoptimizers(OpenEvolve,TTT-
Discover)in0.1×theevaluations,anditsfinalaccuracysurpassestheirsbymorethan10
points(Figure1andTable4). Weattributethisspeeduptotheintentionaldesignchoices
that impose minimum necessary structure on the outer loop (Section 3). In particular,
Meta-Harnesspreservesfullexperiencehistoryusingafilesystemandallowstheproposerto
inspectanythingnecessary,whereasbothOpenEvolveandTTT-Discoveroperatewithmore
structuredandsubstantiallymorelimitedproposerinputsthanfullfilesystemaccess. We
notethatonlinetextclassificationisthesmallest-contextsettingwestudy(Table1),soif
structure-heavytextoptimizersalreadylaghere,theirlimitationsmayonlygrowinharder
regimes.
Meta-Harnessis10×FasterandConvergestoaBetterHarness
Inthissetting,Meta-Harnessmatchesthebestpriortextoptimizers(OpenEvolve,TTT-
Discover) with 10× fewer full evaluations, and its final accuracy surpasses theirs by
morethan10points.
Toisolatewhichpartsoftheproposerinterfacemattermost,wecomparethreeconditions
inonlinetextclassification: ascores-onlycondition,ascores-plus-summaryconditionin
which the proposer receives LLM-generated summaries but no raw traces, and the full
Meta-Harnessinterfacewithaccesstoexecutiontraces(Table3). Theresultsshowalarge
gapinfavorofthefullinterface: scores-onlyreaches34.6medianand41.3bestaccuracy,
whilescores-plus-summaryreaches34.9medianand38.7best. Bycontrast,Meta-Harness
6

Table 1:

Meta-Harnessis10×FasterandConvergestoaBetterHarness



# Page 7

Method Scores Code Summ. Traces Median↑ BestAcc↑ >ZS
✓ ✓
ScoresOnly × × 34.6 41.3 26
✓ ✓ ✓
Scores+Summary × 34.9 38.7 23
Meta-Harness(full) ✓ ✓ - ✓ 50.0 56.7 39
Table3: Ablationoftheinformationavailabletotheproposerinonlinetextclassification. >
ZS:numberofrunswhoseaccuracyexceededthezero-shotbaseline. ThefullMeta-Harness
interfacesubstantiallyoutperformsscores-onlyandscores-plus-summaryablations. Access
torawexecutiontracesisthekeyingredientforenablingharnesssearch.
reaches50.0medianand56.7bestaccuracy,andevenitsmediancandidateoutperformsthe
bestcandidatefoundundereitherablation. Weinterpretthisasevidencethatfullaccess
toexecutiontracesisthemostimportantcomponentoftheinterface: summariesdonot
recoverthemissingsignal,andmayevenhurtbycompressingawaydiagnosticallyuseful
details.
Comparison vs state-of-the-art harnesses. Our pri-
mary points of comparison are hand-designed har- Method Median Best
nessesforthisproblemsetting: AgenticContextEngi- GEPA[1] 32.6 40.2
neering(ACE,Zhangetal.[59]),whichusesreflective Best-of-N 34.0 44.2
memorycurationtobuildcontextovertime,andMeta OpenEvolve[43] 39.1 43.3
ContextEngineering(MCE,Yeetal.[52]),whichmain- TTT-Discover[55] 34.1 45.6
tainsandevolvesalibraryofnatural-languageskills Meta-Harness 50.0 56.7
forcontextconstruction. Asadditionalbaselines,we
evaluatezero-shotpromptingandfew-shotprompting Table 4: Text classification accu-
with N ∈ {4,8,16,32,all} examples. Results in Ta- racies of the harnesses proposed
ble2showthatMeta-Harnessimprovessubstantially bydifferenttextoptimizers(search
over prior hand-designed harnesses. The selected set). Meta-Harness is substan-
Meta-Harness2 reaches48.6%accuracy,outperforming tiallymoreeffectiveatharnessop-
timization.
ACEby7.7pointsandMCEby8.6points. Thesegains
donotcomefromusingmorecontext: Meta-Harnessusesonly11.4Kcontexttokens,versus
50.8KforACEand28.5KforMCE.
Accuracy–ContextTradeoffs. BecauseMeta-Harnessperformsfree-formoptimizationover
harnesscode,wecanexpressajointpreferenceforbothaccuracyandcontextcostrather
thancommittingtoasinglescalarobjectiveinadvance. Givenonlythecurrentmetricsand
thedesiredtrade-off,theproposerisabletodiscoverharnessesacrossabroadrangeofthe
frontier, yieldingasmoothaccuracy–contextParetocurveinFigure3. Thisallowsusto
tradeadditionalcontextforhighertestaccuracyinacontrolledway,ratherthancommitting
toasinglehand-designedoperatingpoint.
Out-of-distribution (OOD) task evaluation. We evaluate whether the discovered har-
nessgeneralizestoentirelynewdatasetsunseenduringsearch. Weconsiderninediverse
datasets,anddescribethemindetailinAppendixC.1. TheselectedMeta-Harnesssystem
achievesthebestaverageaccuracy(73.1%),outperformingACE(70.2%)andallfew-shot
baselines(Table5). Notably,weobservethatnaivelyaddingmorefew-shotexamplesbe-
yond32hurtsperformancein7/9tasks. Meta-Harnessshowsthehighestperformanceon
6/9datasets,suggestingthatthediscoveredharnesscapturesgenerallyeffectivestrategies
fortextclassificationratherthanoverfittingtothespecificdatasetsusedduringsearch.
4.2 HarnessesforRetrieval-AugmentedReasoning
We study a somewhat non-standard setup for olympiad math solving: augmenting the
modelwiththeabilitytoretrieveexamplesfromalargecorpus. Thereisagoodreasonto
expectretrievaltohelpmathematicalreasoninginprinciple,becausesolutionsoftenshare
reusableproofpatterns,sopreviousreasoningtracescontaininformationthatamodelmay
2Weslightlyoverloadterminologyforbrevity:inthetables,Meta-Harnessdenotesthebestdiscov-
eredharness,whereaselsewhereitreferstotheentireharnesssearchprocedure.
7


# Page 8

Harness SciC FiNER Amz5 FPB GoEmo Bank77 News SciT TwHate AvgAcc Ctx↓
Zero-shot 32.7 56.0 52.7 90.0 42.0 80.7 84.7 89.3 75.3 67.0 -
Few-shot(8) 34.0 63.0 54.0 90.0 44.0 82.7 84.7 91.3 76.7 68.9 2.2
Few-shot(32) 38.7 62.0 53.3 90.7 43.3 86.0 85.3 90.7 76.7 69.6 5.2
Few-shot(all) 35.3 61.0 50.0 93.3 42.7 80.7 84.0 90.0 76.7 68.2 7.4
ACE[59] 40.7 74.0 48.0 96.7 44.0 83.3 86.0 90.7 68.7 70.2 11.7
Meta-Harness 53.3 67.0 60.0 94.0 46.0 82.7 86.7 91.3 77.3 73.1 7.3
Table 5: OOD text classification dataset evaluation. We report test accuracy for each
datasetandtheaverageadditionalcontexttokensacrossallninedatasets. Meta-Harness
outperformsthenextbestmethodby2.9pointsonthese9previouslyunseentasks.
Method GPT-5.4n GPT-5.4m Gem-3.1FL Gem-3F GPT-20B Avg.
NoRetriever 23.0 28.8 28.6 42.6 47.6 34.1
DenseRetrieval(k=1) 27.1(+4.1) 24.5(-4.3) 31.3(+2.7) 42.3(-0.3) 46.9(-0.7) 34.4(+0.3)
DenseRetrieval(k=5) 31.1(+8.1) 28.3(-0.5) 37.1(+8.5) 47.2(+4.6) 46.7(-0.9) 38.1(+4.0)
RandomFew-shot 23.1(+0.1) 24.5(-4.3) 31.0(+2.4) 40.4(-2.2) 41.8(-5.8) 32.2(-1.9)
BM25Retrieval 30.2(+7.2) 29.2(+0.4) 32.8(+4.2) 46.6(+4.0) 48.9(+1.3) 37.5(+3.4)
Meta-Harness 31.7(+8.7) 30.4(+1.6) 34.9(+6.3) 46.3(+3.7) 50.6(+3.0) 38.8(+4.7)
Table6: Retrieval-augmentedmathproblemsolvingon200IMO-levelmathproblems. We
showpass@1averagedoverthreesamplesperproblem,withabsoluteimprovementover
thebaselineinparentheses. ThediscoveredMeta-Harnessretrievalstrategyimproves
reasoningontheseIMO-levelproblemsacrossallfiveheld-outmodels,witha4.7-point
averagegainovernoretriever.
beabletoexploitatinferencetime. Yetretrievalhasnotbecomeastandardingredientinthis
setting,andpriorworksuggeststhatithasbeenmuchlesssuccessfulonreasoning-intensive
mathbenchmarksthaninmorefact-groundeddomains[42;49;6]. Thedifficultyisthat
naiveretrievalrarelysurfacestherighttracesintherightform. Thissuggeststhatsuccess
dependslessonaddingretrievalpersethanondiscoveringtherightretrievalpolicy. Rather
thanhand-designingthatpolicy,wegiveMeta-Harnessahardsetofolympiadproblems
andallowtheretrievalbehavioritselftoemergefromsearch.
Theretrievalcorpuscontains≥500,000solvedproblemsfromeightopen-sourcedatasets.
Wecarefullydeduplicatedanddecontaminateditagainstbothevaluationbenchmarksand
thesearchset,confirmedthatheld-outproblemshavenoexactprefixmatchesunderour
string-basedfilter,andmanuallyinspectedtopBM25retrievalsforheld-outexamples(ap-
pendixC.2).WeuseMeta-Harnesstooptimizeaharnessfor40iterationsovera250-problem
searchsetofOlympiad-difficultymathproblems(OlympiadBench+Omni-MATHhard),
producing109candidateretrievalharnesses. WeinitializethesearchpopulationHfrom
themainbaselineharnessesinthissetting: zero-shot,few-shot,andACE.Weselectasingle
harnessbasedonsearch-setperformanceusingGPT-OSS-20B(AppendixB.2). Weevaluate
thisharnesson200previouslyunseenIMO-levelproblemsdrawnfromIMO-AnswerBench,
IMO-ProofBench, and ArXivMath [30; 6]. In addition to GPT-OSS-20B, we evaluate the
sameretrievalharnessonfourmodelsnotseenduringsearch: GPT-5.4-nano,GPT-5.4-mini,
Gemini-3.1-Flash-Lite,andGemini-3-Flash. Wefollowthestandardevaluationprotocol
ofpriorwork[30]andreportaccuracyaveragedoverthreesamplesperproblem.
Results. Table6comparesthediscoveredharnessagainstnoretrieval,denseretrievalusing
theseparateembeddingmodeltext-embedding-3-small,randomfew-shotprompting,and
BM25 retrieval. In contrast, Meta-Harness operates entirely in code space on top of the
sameBM25-basedlexicalretrievalstackasthesparsebaseline,ratherthanintroducingan
additionaldenseencoder. Thediscoveredretrievalharnessoutperformstheno-retrieval
baselineacrossallfiveheld-outmodels,withanaveragegainof4.7points. Italsomatches
orexceedsthestrongestfixedbaselinesonaverage,outperformingBM25retrievalby1.3
pointsoverall,whileavoidingtheregressionsobservedwithdenseretrievalandrandom
few-shotpromptingacrossseveralmodels.
Meta-HarnessImprovesReasoningonIMO-LevelMathProblems
Inretrieval-augmentedmathreasoning,asinglediscoveredretrievalharnesstransfers
across five held-out models, improving accuracy by 4.7 points on average over no
retrievalandyieldingthestrongestoverallaverageamongthecomparedmethods.
8

Table 1:

Meta-HarnessImprovesReasoningonIMO-LevelMathProblems



# Page 9

4.3 EvaluatingAgenticCodingHarnessesonTerminalBench-2
TerminalBench-2 [33] evaluates LLM agents on 89 challenging tasks that require long-
horizon,fullyautonomousexecutionundercomplexdependencies,andsubstantialdomain
knowledge. Prior work has shown that the choice agent harness has a large effect on
performance on this benchmark. We initialize search from two strong open baselines,
Terminus2[33]andTerminus-KIRA[25]. Forthisexperiment,weperformsearchandfinal
evaluationonthesame89-taskbenchmark.Weusethisbenchmarkasadiscoveryproblem[54]
inwhichthegoalistodiscoveraharnessconfigurationthatimprovesperformanceona
hard, publicly contested benchmark. This is standard practice: public writeups already
describerepeatedbenchmark-specificharnessiterationonTerminalBenchitself[18;34;25],
andthebenchmarkissmallandexpensiveenoughthatintroducingaseparatesplitwould
materially weaken the search signal. We additionally check for overfitting by manual
inspectionandregex-basedauditsfortask-specificstringleakageintoevolvedharnesses.
WenotethatalthoughtheresultingharnessisspecializedtotheTerminalBench-2regime,
autonomouscompletionofdifficultlong-horizontasksfromasingleinstructionisacore
capability, and the benchmark consists of many tasks that frontier models and heavily
engineeredharnessesstrugglewith.
Results. We report results on the full bench-
Harness Auto Pass(%)
mark in Table 7, evaluated on two base models:
Claude Opus 4.6andClaude Haiku 4.5. OnOpus Claude Opus 4.6
4.6,Meta-Harnessdiscoversaharnessachieving ClaudeCode × 58.0
76.4%passrate,surpassingthehand-engineered Terminus2 × 62.9
Terminus-KIRA(74.7%)andranking#2amongall Mux × 66.5
Opus 4.6 agents on the TerminalBench-2 leader- Droid × 69.9
TongAgents × 71.9
board. Theonlyhigher-scoringOpus 4.6agentis
MAYA-V2 × 72.1
ForgeCode (81.8%); however, we were unable to
Terminus-KIRA × 74.7
reproducetheirreportedresultfromthepublicly
Capy × 75.3
availablecodealone,suggestingtheirleaderboard ForgeCode × 81.8
scores depend on components beyond the pub-
Meta-Harness ✓ 76.4
lishedrepository. OntheweakerHaiku 4.5model,
theimprovementislarger: Meta-Harnessachieves Claude Haiku 4.5
37.6%,outperformingthenext-bestreportedagent OpenHands × 13.9
(Goose,35.5%)by2.1points. TerminalBench-2is ClaudeCode × 27.5
an actively contested benchmark with multiple Terminus2 × 28.3
teams directly optimizing for it, so the fact that Mini-SWE-Agent × 29.8
Terminus-KIRA × 33.7
anautomaticsearchmethodcanachievebenefits
Goose × 35.5
atthisfrontierisencouragingforlong-horizontext-
optimizationloops. Meta-Harness ✓ 37.6
Qualitativebehavioroftheproposer. Theharness Table 7: Pass rate on TerminalBench-
searchtrajectoryhelpsexplainwhyMeta-Harness 2. Resultsorothersarefromtheoffi-
achievesthesegains; weprovideadetailedsum- cialleaderboard. Meta-Harnessranks
maryinAppendixA.Inearlyiterations,thepro- #2amongallOpus-4.6agentsand#1
poser combined plausible structural fixes with among all Haiku-4.5 agents on this
prompt-templateeditsandobservedthatbothcan- competitivetask.
didatesregressed. Itthenexplicitlyhypothesized
thattheregressionswereconfoundedbythesharedpromptintervention,isolatedthestruc-
tural changes from the prompt rewrite, and ultimately pivoted toward a safer additive
modificationthatbecamethebestcandidateintherun. Thisprovidesqualitativeevidence
thatfilesystemaccessenablestheproposertoinspectpriorexperienceinenoughdetailto
formcausalhypothesesandrevisetheharnessaccordingly.
Meta-HarnessSurpassesHand-EngineeredAgentsonTerminalBench-2
On TerminalBench-2, Meta-Harness automatically discovers harnesses that surpass
Terminus-KIRAonOpus4.6andrank#1amongallHaiku4.5agents.
9

Table 1:

Meta-HarnessSurpassesHand-EngineeredAgentsonTerminalBench-2



# Page 10

5 Discussion
Beyondoutperformingexistingharnesses,Meta-Harnesshasseveralpracticaladvantages.
Discoveredharnessesgeneralizetoout-of-distributionclassificationdatasets(Table5)and
to unseen base models in the math setting (Table 6). A search run completes in a few
hoursofwall-clocktime,yetproducesreadable,transferablestrategiesthatcanbereused
across models, including future, stronger ones. Overfitting in code space is also more
inspectable: brittleif-chainsorhard-codedclassmappingsarevisibleoninspectionina
waythatweight-spaceoverfittingisnot. Morebroadly,ourresultssuggestthatthemain
advantageofMeta-Harnessisnotjustsearchovercode,butsearchwithselectiveaccessto
priordiagnosticexperience. Theproposerisnotlimitedtoscalarrewardsorfixedsummaries;
it can inspect raw code, execution traces, and prior failures, then use that information
toformandtesthypothesesaboutwhattochange. Thequalitativesearchtrajectoriesin
AppendixA.2illustratethisbehaviordirectly.
Our findings reflect a recurring pattern in machine learning [45]: once a search space
becomes accessible, stronger general-purpose agents can outperform hand-engineered
solutions. Anaturalnextstepforfutureworkistoco-evolvetheharnessandthemodel
weights,lettingthestrategyshapewhatthemodellearnsandviceversa. Whileweevaluate
onthreediversedomains,ourexperimentsdemonstratethatharnesssearchcanworkwith
oneparticularlystrongcoding-agentproposer(ClaudeCode);abroaderstudyofhowthe
effectvariesacrossproposeragentsremainsforfuturework.
10


# Page 11

Acknowledgements
We thank KRAFTON AI for providing API credit support. This work is supported by
OpenAI,KFAS,andSchmidtSciencesAI2050. WethankAnikaitSinghandJubayerIbn
Hamidfortheirvaluablefeedbackandsuggestions,andSiennaJ.Leeforpatientlylistening
toYL’shalf-formedthoughtsduringtheearlystagesofthiswork.
References
[1] Lakshya A Agrawal, Shangyin Tan, Dilara Soylu, Noah Ziems, Rishi Khare, Krista
Opsahl-Ong,ArnavSinghvi,HerumbShandilya,MichaelJRyan,MengJiang,etal.
Gepa: Reflective prompt evolution can outperform reinforcement learning. arXiv
preprintarXiv:2507.19457,2025.
[2] EkinAkyu¨rek,DaleSchuurmans,JacobAndreas,TengyuMa,andDennyZhou. What
learningalgorithmisin-contextlearning? investigationswithlinearmodels,2023. URL
https://arxiv.org/abs/2211.15661.
[3] MarcinAndrychowicz,MishaDenil,SergioGomez,MatthewWHoffman,DavidPfau,
TomSchaul,BrendanShillingford,andNandoDeFreitas.Learningtolearnbygradient
descentbygradientdescent. Advancesinneuralinformationprocessingsystems,29,2016.
[4] Anthropic. Claudecode: Anagenticcodingtool. https://www.anthropic.com/claude
-code,2025.
[5] Anthropicandcommunitycontributors. agentskills/agentskills. GitHubrepository
https://github.com/agentskills/agentskills. Specificationanddocumentationfor
AgentSkills,accessedMarch27,2026.
[6] MislavBalunovic´,JasperDekoninck,IvoPetrov,NikolaJovanovic´,andMartinVechev.
Matharena: Evaluatingllmsonuncontaminatedmathcompetitions,February2025.
URLhttps://matharena.ai/.
[7] FrancescoBarbieri,JoseCamacho-Collados,LeonardoNeves,andLuisEspinosa-Anke.
Tweeteval: Unifiedbenchmarkandcomparativeevaluationfortweetclassification,
2020. URLhttps://arxiv.org/abs/2010.12421.
[8] LucaBeurer-Kellner,MarcFischer,andMartinVechev. Promptingisprogramming:
Aquerylanguageforlargelanguagemodels. ProceedingsoftheACMonProgramming
Languages,7(PLDI):1946–1969,June2023. ISSN2475-1421. doi: 10.1145/3591300. URL
http://dx.doi.org/10.1145/3591300.
[9] BirgittaBo¨ckeler. Harnessengineering. https://martinfowler.com/articles/explor
ing-gen-ai/harness-engineering.html,March2026. martinfowler.com.
[10] CanBo¨lu¨k. Iimproved15LLMsatcodinginoneafternoon.onlytheharnesschanged.
https://blog.can.ac/2026/02/12/the-harness-problem/,February2026.
[11] In˜igoCasanueva,TadasTemcˇinas,DanielaGerz,MatthewHenderson,andIvanVulic´.
Efficientintentdetectionwithdualsentenceencoders,2020. URLhttps://arxiv.org/
abs/2003.04807.
[12] Mert Cemri, Shubham Agrawal, Akshat Gupta, Shu Liu, Audrey Cheng, Qiuyang
Mang,AshwinNaren,LutfiErenErdogan,KoushikSen,MateiZaharia,etal. Adae-
volve: Adaptivellmdrivenzeroth-orderoptimization. arXivpreprintarXiv:2602.20133,
2026.
[13] HarrisonChase. Langchain,October2022. URLhttps://github.com/langchain-ai/
langchain. Software,released2022-10-17.
[14] ArmanCohan, WaleedAmmar,MadeleinevanZuylen, andFieldCady. Structural
scaffoldsforcitationintentclassificationinscientificpublications,2019. URLhttps:
//arxiv.org/abs/1904.01608.
11


# Page 12

[15] Dorottya Demszky, Dana Movshovitz-Attias, Jeongwoo Ko, Alan Cowen, Gaurav
Nemade,andSujithRavi. Goemotions: Adatasetoffine-grainedemotions,2020. URL
https://arxiv.org/abs/2005.00547.
[16] Zhiwei Fei, Xiaoyu Shen, Dawei Zhu, Fengzhe Zhou, Zhuo Han, Alan Huang,
Songyang Zhang, Kai Chen, Zhixin Yin, Zongwen Shen, et al. Lawbench: Bench-
markinglegalknowledgeoflargelanguagemodels. InProceedingsofthe2024conference
onempiricalmethodsinnaturallanguageprocessing,pp.7933–7962,2024.
[17] ChelseaFinn,PieterAbbeel,andSergeyLevine. Model-agnosticmeta-learningforfast
adaptationofdeepnetworks. InInternationalConferenceonMachineLearning,2017.
[18] ForgeCode. Benchmarksdon’tmatter,2025. URLhttps://forgecode.dev/blog/bench
marks-dont-matter/.
[19] GretelAI. Symptomtodiagnosisdataset. https://huggingface.co/datasets/gretel
ai/symptom to diagnosis,2023. Accessed: 2026-01-22.
[20] Shengran Hu, Cong Lu, and Jeff Clune. Automated design of agentic systems. In
The Thirteenth International Conference on Learning Representations, 2025. URL https:
//openreview.net/forum?id=t9U3LW7JVX.
[21] AnthropicJustinYoung. Effectiveharnessesforlong-runningagents. https://anthro
pic.com/engineering/effective-harnesses-for-long-running-agents,November
2025. AnthropicEngineeringBlog.
[22] Phillip Keung, Yichao Lu, Gyo¨rgy Szarvas, and Noah A. Smith. The multilingual
amazonreviewscorpus,2020. URLhttps://arxiv.org/abs/2010.02573.
[23] Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Keshav San-
thanam, Sri Vardhamanan, Saiful Haq, Ashutosh Sharma, Thomas T. Joshi, Hanna
Moazam, Heather Miller, Matei Zaharia, and Christopher Potts. Dspy: Compil-
ing declarative language model calls into self-improving pipelines, 2023. URL
https://arxiv.org/abs/2310.03714.
[24] Tushar Khot, Ashish Sabharwal, and Peter Clark. Scitail: A textual entailment
dataset from science question answering. Proceedings of the AAAI Conference on
Artificial Intelligence, 32(1), Apr. 2018. doi: 10.1609/aaai.v32i1.12022. URL
https://ojs.aaai.org/index.php/AAAI/article/view/12022.
[25] KRAFTONAIandLudoRobotics.Terminus-kira:Boostingfrontiermodelperformance
onterminal-benchwithminimalharness,2026. URLhttps://github.com/krafton-a
i/kira.
[26] Yoonho Lee, Joseph Boen, and Chelsea Finn. Feedback descent: Open-ended text
optimizationviapairwisecomparison. InarXivpreprintarXiv:2511.07919,2025.
[27] Joel Lehman, Jonathan Gordon, Shawn Jain, Kamal Ndousse, Cathy Yeh, and Ken-
nethO.Stanley. Evolutionthroughlargemodels,2022. URLhttps://arxiv.org/abs/
2206.08896.
[28] PatrickLewis,EthanPerez,AleksandraPiktus,FabioPetroni,VladimirKarpukhin,
Naman Goyal, Heinrich Ku¨ttler, Mike Lewis, Wen-tau Yih, Tim Rockta¨schel, et al.
Retrieval-augmentedgenerationforknowledge-intensivenlptasks. Advancesinneural
informationprocessingsystems,33:9459–9474,2020.
[29] LefterisLoukas,ManosFergadiotis,IliasChalkidis,EiriniSpyropoulou,Prodromos
Malakasiotis,IonAndroutsopoulos,andGeorgiosPaliouras. Finer: Financialnumeric
entity recognition for xbrl tagging. In Proceedings of the 60th Annual Meeting of the
AssociationforComputationalLinguistics(Volume1: LongPapers),pp.4419–4431.Associa-
tionforComputationalLinguistics,2022. doi: 10.18653/v1/2022.acl-long.303. URL
http://dx.doi.org/10.18653/v1/2022.acl-long.303.
12


# Page 13

[30] ThangLuong,DawsenHwang,HoangH.Nguyen,GolnazGhiasi,YuriChervonyi,In-
suk Seo, Junsu Kim, Garrett Bingham, Jonathan Lee, Swaroop Mishra, Alex Zhai,
Clara Huiyi Hu, Henryk Michalewski, Jimin Kim, Jeonghyun Ahn, Junhwi Bae,
XingyouSong,TrieuH.Trinh,QuocV.Le,andJunehyukJung. Towardsrobustmathe-
maticalreasoning. InProceedingsofthe2025ConferenceonEmpiricalMethodsinNatural
LanguageProcessing,2025. URLhttps://aclanthology.org/2025.emnlp-main.1794/.
[31] Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah
Wiegreffe,UriAlon,NouhaDziri,ShrimaiPrabhumoye,YimingYang,etal. Self-refine:
Iterativerefinementwithself-feedback.Advancesinneuralinformationprocessingsystems,
36:46534–46594,2023.
[32] PekkaMalo,AnkurSinha,PyryTakala,PekkaKorhonen,andJyrkiWallenius. Good
debt or bad debt: Detecting semantic orientations in economic texts, 2013. URL
https://arxiv.org/abs/1307.5336.
[33] Mike A Merrill, Alexander G Shaw, Nicholas Carlini, Boxuan Li, Harsh Raj, Ivan
Bercovich,LinShi,JeongYeonShin,ThomasWalshe,EKellyBuchanan,etal. Terminal-
bench: Benchmarkingagentsonhard,realistictasksincommandlineinterfaces. arXiv
preprintarXiv:2601.11868,2026.
[34] Jack Nichols. How we scored #1 on terminal-bench (52%), Jun 2025. URL https:
//www.warp.dev/blog/terminal-bench.
[35] AlexanderNovikov,NgaˆnVu˜,MarvinEisenberger,EmilienDupont,Po-SenHuang,
AdamZsoltWagner,SergeyShirobokov,BorislavKozlovskii,FranciscoJRRuiz,Abbas
Mehrabian,etal. Alphaevolve: Acodingagentforscientificandalgorithmicdiscovery.
arXivpreprintarXiv:2506.13131,2025.
[36] OpenAI. Harness engineering: leveraging Codex in an agent-first world. https:
//openai.com/index/harness-engineering/,February2026. OpenAIBlog.
[37] CharlesPacker,VivianFang,Shishir GPatil,KevinLin,SarahWooders,andJoseph E
Gonzalez. Memgpt: Towardsllmsasoperatingsystems. 2023.
[38] Reid Pryzant, Dan Iter, Jerry Li, Yin Tat Lee, Chenguang Zhu, and Michael Zeng.
Automatic prompt optimization with “gradient descent” and beam search. arXiv
preprintarXiv:2305.03495,2023.
[39] BernardinoRomera-Paredes,MohammadaminBarekatain,AlexanderNovikov,Matej
Balog, M Pawan Kumar, Emilien Dupont, Francisco JR Ruiz, Jordan S Ellenberg,
PengmingWang,OmarFawzi,etal. Mathematicaldiscoveriesfromprogramsearch
withlargelanguagemodels. Nature,625(7995):468–475,2024.
[40] Jurgen Schmidhuber. A neural network that embeds its own meta-levels. In IEEE
InternationalConferenceonNeuralNetworks,1993.
[41] NadineSchneider,NikolausStiefl,andGregoryALandrum. What’swhat:The(nearly)
definitiveguidetoreactionroleassignment. Journalofchemicalinformationandmodeling,
56(12):2336–2346,2016.
[42] Srijan Shakya, Anamaria-Roberta Hartl, Sepp Hochreiter, and Korbinian Po¨ppel.
Adaptive retrieval helps reasoning in llms – but mostly if it’s not used, 2026. URL
https://arxiv.org/abs/2602.07213.
[43] AsankhayaSharma. Openevolve: anopen-sourceevolutionarycodingagent. https:
//github.com/algorithmicsuperintelligence/openevolve, 2025. URL https:
//github.com/algorithmicsuperintelligence/openevolve. GitHubrepository.
[44] JakeSnell,KevinSwersky,andRichardS.Zemel. Prototypicalnetworksforfew-shot
learning. InAdvancesinNeuralInformationProcessingSystems,2017.
[45] RichSutton. Thebitterlesson,2019. URLhttp://www.incompleteideas.net/IncIdeas/Bitter-
Lesson.html,2019.
13


# Page 14

[46] SebastianThrunandLorienPratt. Learningtolearn: Introductionandoverview. In
Learningtolearn,pp.3–17.Springer,1998.
[47] Muxin Tian, Zhe Wang, Blair Yang, Zhenwei Tang, Kunlun Zhu, Honghua Dong,
HanchenLi,XinniXie,GuangjingWang,andJiaxuanYou. Swe-benchmobile: Can
largelanguagemodelagentsdevelopindustry-levelmobileapplications? InarXiv
preprint,2026. URLhttps://api.semanticscholar.org/CorpusID:285462974.
[48] HarshTrivedi,NiranjanBalasubramanian,TusharKhot,andAshishSabharwal. Inter-
leavingretrievalwithchain-of-thoughtreasoningforknowledge-intensivemulti-step
questions,2023. URLhttps://arxiv.org/abs/2212.10509.
[49] ChenghaoXiao,GThomasHudson,andNouraAlMoubayed. Rar-b: Reasoningas
retrievalbenchmark,2024. URLhttps://arxiv.org/abs/2404.06347.
[50] YimingXiong,ShengranHu,andJeffClune. Learningtocontinuallylearnviameta-
learningagenticmemorydesigns. InOpenReview,2026. URLhttps://api.semanticsc
holar.org/CorpusID:285454009.
[51] Chengrun Yang, Xuezhi Wang, Yifeng Lu, Hanxiao Liu, Quoc V Le, Denny Zhou,
andXinyunChen. Largelanguagemodelsasoptimizers. InTheTwelfthInternational
ConferenceonLearningRepresentations,2023.
[52] HaoranYe,XuningHe,VincentArak,HaonanDong,andGuojieSong. Metacontext
engineeringviaagenticskillevolution. arXivpreprintarXiv:2601.21557,2026.
[53] Mert Yuksekgonul, Federico Bianchi, Joseph Boen, Sheng Liu, Zhi Huang, Carlos
Guestrin,andJamesZou. Textgrad: Automatic”differentiation”viatext,2024. URL
https://arxiv.org/abs/2406.07496.
[54] MertYuksekgonul,DanielKoceja,XinhaoLi,FedericoBianchi,JedMcCaleb,Xiaolong
Wang,JanKautz,YejinChoi,JamesZou,CarlosGuestrin,andYuSun. Learningto
discoverattesttime,2026. URLhttps://arxiv.org/abs/2601.16175.
[55] MertYuksekgonul,DanielKoceja,XinhaoLi,FedericoBianchi,JedMcCaleb,Xiaolong
Wang,JanKautz,YejinChoi,JamesZou,CarlosGuestrin,etal. Learningtodiscoverat
testtime. arXivpreprintarXiv:2601.16175,2026.
[56] AlexL.Zhang,TimKraska,andOmarKhattab. Recursivelanguagemodels,2026. URL
https://arxiv.org/abs/2512.24601.
[57] GuibinZhang,HaotianRen,ChongZhan,ZhenhongZhou,JunhaoWang,HeZhu,
WangchunshuZhou,andShuichengYan. Memevolve: Meta-evolutionofagentmem-
orysystems. arXivpreprintarXiv:2512.18746,2025.
[58] JiayiZhang, JinyuXiang, ZhaoyangYu, FengweiTeng, XionghuiChen, JiaqiChen,
MingchenZhuge,XinCheng,SiruiHong,JinlinWang,BingnanZheng,BangLiu,Yuyu
Luo,andChenglinWu. Aflow: Automatingagenticworkflowgeneration,2025. URL
https://arxiv.org/abs/2410.10762.
[59] QizhengZhang,ChangranHu,ShubhangiUpasani,BoyuanMa,FengluHong,V.Ka-
manuru,JayRainton,ChenWu,MengmengJi,HanchenLi,UrmishThakker,James
Zou, and K. Olukotun. Agentic context engineering: Evolving contexts for self-
improvinglanguagemodels. InarXivpreprintarXiv:2510.04618,2025.
[60] XiangZhang,JunboZhao,andYannLeCun. Character-levelconvolutionalnetworks
fortextclassification,2016. URLhttps://arxiv.org/abs/1509.01626.
14


# Page 15

55
50
45
40
35
30
0 10 20 30 40
Harness Evaluations
)%(
ecnamrofreP
tseB
Harness Optimizer Search Progress
Meta-Harness
TTT-Discover
Best-of-N
OpenEvolve
ACE
GEPA
Few-shot
Zero-shot
Figure4: Search-setaccuracyoverevaluationsforallcomparedtextoptimizersononline
textclassification.Eachpointisonecandidateharness;linestrackthebest-so-far.Per-dataset
curvesareshownalongsidetheaggregate. Meta-Harnessreachesthefinalaccuracyof
OpenEvolveandTTT-Discoverwithinthefirst4evaluationsandcontinuesimproving,
endingmorethan10pointsaboveallbaselines.
A QualitativeProposerBehavior
Thissectionexamineshowtheproposerusesthefilesystemduringsearch,drawingonthe
TerminalBench-2run(10iterations,Claude Opus 4.6).
A.1 FileAccessStatistics
Toverifythattheproposermakessubstantiveuseofthefilesystemratherthandefaultingto
localedits,werecordedallfilereadsperiteration.
Table 8 summarizes the results. The proposer reads a median of 82 files per iteration
(range69–99),roughlyevenlysplitbetweenpriorharnesssourcecode(41%)andexecution
traces(40%),withtheremaindergoingtoscoresummaries(6%)andotherfiles(13%). This
confirms that the proposer’s access pattern is non-Markovian: it routinely inspects the
majorityofavailablehistoryratherthanconditioningonlyonthemostrecentparent.
Statistic Value
Filesreadperiteration(median) 82
Filesreadperiteration(range) 69–99
Filetypebreakdown
Harnesssourcecode 41%
Executiontraces 40%
Score/summaryfiles 6%
Other 13%
Table8: ProposerfileaccessstatisticsfromtheTerminalBench-2searchrun(10iterations,
Claude Opus 4.6). Theproposerreadsextensivelyfromthefilesystem,withroughlyequal
attentiontopriorsourcecodeandexecutiontraces.
15


# Page 16

A.2 QualitativeBehavior: CausalReasoningOverPriorFailures
TheTerminalBench-2searchlogrevealsaclearnarrativearcinwhichtheproposerlearns
fromitsownregressions. Ratherthanwanderingrandomlythroughlocaledits,itforms
an explicit diagnosis of why early candidates failed, then shifts toward a safer design
pattern. Alltextinsidethelogboxesbelowisquotedverbatimfromtheproposer’srecorded
reasoningateachiteration(emphasisours).
Iterations1–2:promisingbugfixesareconfoundedbypromptedits.Thefirsttwoiterations
bothbundleplausiblestructuralfixeswithprompt-templatemodifications,andbothregress
sharplyfromthe64.4%Terminus-KIRAbaseline. Iteration1targetsobservationcorruption
fromleakedterminalmarkersandaddsaloopbreaker:
Hypothesis: CMDEND marker fragments leak into LLM observations on long-running
tasks, causing the model to get confused and enter infinite no-tool-call loops.
Stripping these markers + adding a loop breaker will recover wasted steps.
Thatcandidatealsointroducedanewcleanup-orientedprompttemplateandaverification
checklist. Iteration2proposesadifferentstate-machinefix:
Double-confirmation completion mechanism causes verification spirals. Observed in
trajectories where the agent solves the task early but burns 15--40+ additional steps
re-verifying because each verification command resets pending completion, requiring
another task complete → checklist → verify cycle.
Thissecondcandidateremovesthepending-completionmechanismentirely, whilealso
carryingoverthemarkerstrippingandthenewprompt. Itstillregresses,whichgivesthe
proposertwofailedcandidateswithdifferentstructuralchangesbutonesharedprompt
intervention.
Iteration3: theproposeridentifiestheconfound. Byiteration3,theproposerexplicitly
infersthattheregressionsarenotprimarilyduetothestructuralbugfixesthemselves:
Prior attempts: evo marker fix (58.9%, -5.6pp), evo single confirm (57.8%, -6.7pp)
--- both regressed. Root cause of regressions: Prompt template changes (cleanup
directives) caused the agent to delete necessary state before task completion. The
structural bugfixes were confounded with harmful prompt changes. evo strip only
isolates the two proven structural fixes.
Thisisthekeycausalstepinthetrajectory. Theproposernoticesthatthecommonfactor
across the first two failures is not the particular bugfix, but the cleanup-heavy prompt
rewrite. Itthereforerevertstotheoriginalpromptandtestsonlythemarker-strippingand
loop-breaker. Theresultingcandidatestillunderperformsslightly(63.3%,-1.1pp),butit
losesfarlessthantheearlierversions,whichsupportstheconfounddiagnosis.
Iterations 4–6: direct fixes to the diagnosed failure mode still regress. The next three
iterationscontinuetoprobethesamepartofthedesignspace,butnowwithmoreexplicit
theoriesaboutwhythecompletionlogicisfragile. Iteration4attributesfailurestoaconcrete
state-machinebuginwhichverificationcommandsresetthecompletionflagandtrapthe
agentinrepeatedchecklistcycles:
Remove the two self. pending completion = False lines that reset the completion
flag when intermediate commands run. This fixes a state machine bug where: (1)
Agent calls task complete → sees QA checklist, pending completion = True (2) Agent
runs verification commands → pending completion = False (bug!) (3) Agent calls
task complete again → sees checklist AGAIN → infinite loop.
Theproposerevencitesconcretetrajectoryevidence,notingthatconfigure-git-webserver
producedbaselinefailureswithagentsstuckin30–60stepverificationspiralsaftereffec-
tivelysolvingthetask. Iteration5triestosoftenthecleanuplanguagewhilepreserving
16


# Page 17

confirmation,butstilleditsthepromptandregressesbadly. Iteration6returnstothesafer
evo strip onlybaseandproposesasystems-leveloptimization:
Empty-command turns waste full LLM round-trips when terminal output hasn’t changed.
Smart-waiting (poll pane up to 3×5s) before the next LLM call saves 5--15 turns on
long-running tasks.
That change also regresses. By this point, the proposer has learned a specific empirical
lesson: modificationstopromptsandcompletionflowarehighrisk,evenwhenthelocal
hypothesissoundsreasonable.
Iteration7: thewinningcandidate. Aftersixconsecutiveregressions,theproposershifts
strategyfrommodifyingthecontrollooptoaddinginformationbeforetheloopbegins:
All 6 prior iterations regressed from the 64.4% baseline because they modified the
completion flow, prompt template, or observation processing. evo env bootstrap takes
a different approach --- purely additive. It gathers an environment snapshot via a
single shell command before the first LLM call and appends it to the initial prompt.
No other methods are changed. This should eliminate 3--5 wasted exploration turns on
dependency-heavy tasks without risking regression on already-passing tasks.
Thiscandidateisthebestresultsofar. Theimportantpointisnotjustthatiteration7wins,
butthattheproposerarticulateswhyitshouldbesafer: itavoidstouchingthepreviously
fragilecompletionmachineryandinsteadaddsinformationthatisusefulmainlyonhard
tasks.
Iteration 8: composition. Having found one additive improvement, the proposer next
attemptstocomposeitwithanearlierstructuralfix:
Combining two orthogonal fixes --- env snapshot (saves early exploration turns) +
marker stripping with no-tool-call loop breaker --- will yield +1--3pp because they
address independent failure modes without touching prompts or confirmation flows
(which caused regressions in 5 of 7 prior iterations).
Iteration 10: cross-run transfer. The proposer references results from a separate earlier
searchrun:
The evolution history showed ‘‘don’t cleanup service artifacts’’ was worth +18pp. Iter
9 (evo no cleanup directive) targeted the same idea but crashed before evaluation.
Summary. Thesearchtrajectorydemonstratesthattheproposerdoesmorethanrandom
mutation. Across the first seven iterations, it identifies a confound, tests the confound-
isolatinghypothesisdirectly,observesthatcontrol-flowandprompteditsremainfragile,and
thendeliberatelypivotstoapurelyadditivemodificationthatbecomesthebestcandidate
intherun. Itsubsequentlytriestocomposethatwinningideawithearlierfixesandeven
transferslessonsacrossruns. Thiskindofcausalreasoningoverpriorfailuresisprecisely
what full-history filesystem access enables and what compressed-feedback optimizers
cannotsupport.
B DiscoveredHarnesses
Meta-Harnessdiscoversexecutableinference-timeproceduresspecifictotheproblemsetup
athand. Theseharnessesarestructured,domain-specificpolicies,oftenwithnontrivialcon-
trolflowsuchasrouting,filtering,andconditionalcontextconstruction,selectedsolelyby
whethertheyimprovesearch-setperformance. Thissectionpresentscompact,method-style
abstractionsofrepresentativeharnessesthatsummarizethemainbehaviorsandcontrol-
flowdecisionsthatdriveinference-timebehavior. Forreference,thefullimplementationfor
eachdiscoveredharnessisontheorderof100–1000linesofcode.
17


# Page 18

Query+memory
Retrieveconfirmers
Retrievetop-5
(=D)andchallengers
similarexamples
(̸=D)
D
Draftcall Verificationcall
initiallabelD keeporreviseD
Finallabel
Figure5: Draft-verificationclassificationharness. Thefirstcallproducesadraftlabelfrom
ashortretrievedcontext. Thesecondcallretrievesevidenceforandagainstthatdraftand
returnsthefinalprediction.
B.1 TextClassificationHarness
Inonlinetextclassification,Meta-Harnessdiscoversafamilyofmemory-basedharnesses
ratherthanasinglecanonicalpolicy. Table9reportstheParetofrontierofnon-dominated
variantsfromthemainsearch,allselectedsolelybysearch-setperformance. Wehighlight
tworepresentativeendpointshere:Meta-Harness (Draft Verification),thelowest-context
frontierpoint,andMeta-Harness (Label-Primed Query),thehighest-accuracyfrontierpoint
usedinthemaintext.
Overview. Both harnesses maintain a growing memory of past labeled examples and
buildpromptsfromthatmemoryatinferencetime. Whatdiffersisthecontrolflowusedto
interrogatethememory. Meta-Harness (Draft Verification)usestwoshortcallsandex-
plicitlyteststhemodel’sfirstguessagainstretrievedcounterexamples,whileMeta-Harness
(Label-Primed Query)spendsalargersingle-callbudgetonmakingthelabelspaceand
localdecisionboundariesexplicit. Figures5and6summarizethesetwoprograms.
Meta-Harness(DraftVerification). Thecorrespondingdiscoveredfileisdraft verificat
ion.py. Thislightweightvariantturnspredictionintoatwo-callprocedure. Itfirstretrieves
the5mostsimilarlabeledexamplesandmakesadraftprediction. Itthenre-queriesthe
samememoryconditionedonthatdraftlabel,retrieving5confirmerswiththesamelabel
and5challengerswithdifferentlabels,andasksthemodelwhethertomaintainorreviseits
initialanswer. Thekeydiscoveredbehavioristhatthesecondretrievaldependsonboththe
queryandthedraftprediction,sotheharnesscansurfacecounterexamplestargetedatthe
model’scurrentguessratherthanonlygenericnearneighbors. Iftoofewlabeledexamples
havebeenaccumulated,theprogramfallsbacktoastandardsingle-callfew-shotprompt.
• Stage1: Draft. Retrievethe5nearestlabeledexamplesandaskforaninitialprediction.
• Stage2: Verification. Conditionretrievalonthedraftlabel,thenshowbothsupporting
andchallengingexamplesbeforemakingthefinalprediction.
• Coldstart. Iffewerthan5labeledexamplesareavailable,skipthetwo-stageprocedure
anduseastandardsingle-callfew-shotprompt.
• Whyitischeap. Bothcallsuseshortretrievedcontexts,sotheoverallcontextcoststays
nearthelowendofthefrontierevenwithtwomodelinvocations.
18


# Page 19

Query+memory
Labelprimer TF-IDFretrieval
allvalidlabels query-anchoredpairing
Contrastivepairs
Coverageblock
similarexamples
bestexampleperlabel
differentlabels
Assembleonepromptwithprimer,
coverage,andcontrastivepairs
Finallabel
Figure 6: Label-primed query-anchored classification harness. The program builds a
singlepromptthatexposesthelabelspace,thenpopulatesitwithquery-relevantcoverage
examplesandlocalcontrastivepairs.
Meta-Harness(Label-PrimedQuery). Thecorrespondingdiscoveredfileislabel prime
d query anchored.py. Thisstrongestvariantusesasinglelargercallbuiltfromthreeparts.
Itbeginswithalabelprimerlistingthevalidoutputlabels,thenconstructsacoveragesection
withonequery-relevantexampleperlabel,andfinallyaddsquery-anchoredcontrastivepairs
thatplacehighlysimilarexampleswithdifferentlabelssidebyside. Thecoverageblock
exposesthefulllabelspace,whilethecontrastiveblocksharpenslocaldecisionboundaries
aroundthecurrentquery. Incode,theharnessimplementsthiswithTF-IDFretrievalover
pastlabeledexamplesandaquery-anchoredpairingrulethatchoosescontrastingexamples
fromthesamelocalneighborhood.
• Labelprimer. Listthevalidoutputlabelsbeforeshowinganyexamples,sothemodel
seesthefullanswerspaceupfront.
• Coverageblock. Foreachknownlabel,retrievethemostquery-relevantlabeledexample
andincludeonerepresentativeexampleperclass.
• Contrastiveblock. Buildpairsofhighlysimilarexampleswithdifferentlabels,sothe
promptexposeslocaldecisionboundariesaroundthecurrentquery.
• Retrievalrule. UseTF-IDFsimilarityandquery-anchoredpartnerselectionratherthan
label-agnosticnearestneighbors.
B.2 MathRetrievalHarness
ThissubsectiondescribestheretrievalharnessdiscoveredbyMeta-Harnessformathematical
reasoning(Section4.2). Thefinalharnessisacompactfour-routeBM25programwhose
structureemergedthroughsearchratherthanbeingmanuallyspecifiedafterthefact. All
designchoicesbelow—theroutingpredicates,rerankingterms,deduplicationthresholds,
and per-route example counts—were selected by the outer loop across 40 iterations of
evolution.
19


# Page 20

Datasets Avgmetrics
Variant USPTO↑ Symptom↑ LawBench↑ Avg↑ Ctx↓
Meta-Harness (Draft Verification) 18.0 85.4 17.0 40.1 5.4
Meta-Harness (Error-Annotated) 9.0 87.7 24.0 40.2 22.3
Meta-Harness (CoT Replay) 13.0 88.2 25.0 42.1 23.3
Meta-Harness (Cluster Coverage) 12.0 86.8 33.0 43.9 31.2
Meta-Harness (Cascade Retrieval) 12.0 86.8 36.0 44.9 39.2
Meta-Harness (RRF + Contrastive) 18.0 89.6 35.0 47.5 41.4
Meta-Harness (Relevance + Contrastive) 18.0 90.6 36.0 48.2 43.9
Meta-Harness (Label-Primed Query) 14.0 86.8 45.0 48.6 45.5
Table9: Pareto-optimaldiscoveredvariantsfromthemaintext-classificationsearch,trad-
ing off average accuracy against context cost. The selected system in the main text is
Meta-Harness (Label-Primed Query). Ctxdenotesaverageadditionalcharactersininput
context(thousands).
Figure7: Search-setvs.testaccuracyperdatasetfordiscoveredtext-classificationstrategies.
Eachpinkdotisadiscoveredstrategy;baselinesarelabeled. Thedasheddiagonalisy=x.
Overview. At inference time, the harness assigns each problem to exactly one of four
routes: combinatorics,geometry,numbertheory,oradefaultrouteforalgebraandother
problems. Thegatesareimplementedaslightweightlexicalpredicatesovertheproblem
statement, including keyword sets and a small number of regex features for geometry
notation.Theharnessdoesnotaggregateoutputsacrossroutes:oncearouteisselected,only
thatrouteretrievesexamplesforthefinalprompt. AllroutesuseBM25astheunderlying
retrieval mechanism over the filtered corpus described above. The BM25 index uses a
math-awaretokenizerthatpreservesLaTeXtokens(e.g.,\frac,ˆ{2})asatomicunits. The
selected harness is a merge of two successful search lineages, autonomously combined
bytheproposerduringsearch: onecontributedastrongergeometryroutebasedonraw
BM25,whileanothercontributedastrongercombinatoricsroutebasedondeduplication
anddifficultyreranking. Figure8givesacompactflowchartviewofthefinalprogram.
• Combinatorics: fetch20BM25candidates,deduplicateto8,rerankbylexicalscoreand
difficulty,thenreturnthetop3. Thisisthemainroutewheretheharnessexplicitlytrades
offdiversityagainsthard-problemmatching.
• Geometry: return1hardNuminaMathreferencetogetherwith2rawBM25neighbors.
Searchconsistentlyprefersrawstructuralmatcheshereoverdifficultyreranking.
• Numbertheory: fetch12BM25candidatesandrerankusinglexicalscore,difficulty,anda
smallbonusforsolutionsthatstateatechniqueearly. Thisfavorsexampleswhoseproof
strategyisexplicit.
• Default: fetch10BM25candidates,rerankbylexicalscoreanddifficulty,andchoosean
adaptivenumberofexamplesbasedonhowconcentratedthetopretrievalscoresare.
20


# Page 21

Query
Lexicalrouter
keywordandregexcues
Combinatorics
Numbertheory Algebra/Other
BM25@20 Geometry
BM25@12 BM25@10
Dedupto8 1fixedref+2BM25
Rerank Rerank
Rerank Norerank Keep3 AdaptiveK
Keep3
Buildfinalprompt
Figure8: Discoveredmathretrievalharness. Alexicalrouterassignseachquerytoone
offoursubject-specificretrievalpolicies. Theselectedpolicyretrievesexamples,whichare
insertedintothefinalprompt.
B.3 TerminalBench-2Harness
ThediscoveredTerminalBench-2harnessbuildsonTerminus-KIRA[25],inheritingitsnative
toolcalling(replacingTerminus2’sICL-basedJSONparsing),30KBoutputcap,andmulti-
perspectivecompletionchecklist. ThemainmodificationdiscoveredbyMeta-Harnessis
environmentbootstrapping: beforetheagentloopbegins,theharnessrunsacompound
shell command to gather a snapshot of the sandbox environment and injects it into the
initialprompt. Theproposer’shypothesis,recordedverbatimfromthesearchlog,was:
Hypothesis: ‘‘Injecting an environment snapshot (OS, installed languages, package
managers, /app contents) before the first LLM turn will reduce wasted exploration
episodes by 3--5 turns on dependency-heavy tasks’’
Changes: ‘‘Added gather env snapshot() that runs a single compound shell command to
collect working directory, /app listing, available languages (python, gcc, node, java,
rustc, go), package managers (pip, apt) [...] and injects as [Environment Snapshot]
block’’
Thesnapshotincludes: theworkingdirectory,alistingof/app(truncatedto20entriesfor
largedirectories),availableprogramminglanguagesandtheirversions(Python,GCC,G++,
Node,Java,Rust,Go),installedpackagemanagers(pip,apt-get),andavailablememory.
Thiseliminatesthe2–4exploratoryturnsthatagentstypicallyspenddiscoveringwhattools
and files are available, allowing the model to begin productive work immediately. The
bootstrappingcommandisguardedbya15-secondtimeoutandfailssilently,soitdoesnot
breaktheagentinunusualenvironments. Thefullimplementationaddsroughly80lineson
topofTerminus-KIRA.Figure9summarizestheharnessstructure.
Per-taskanalysis. ComparedtoTerminus-KIRA,thediscoveredharnessgainson7of89
tasks,withthelargestimprovementsonprotein-assemblyandpath-tracing. Thegaining
tasksshareacommonproperty: theyrequiredomain-specifictoolingwhoseavailability
cannotbeassumedinadvance(bioinformaticslibraries,renderingpipelines,chessengines,
cryptographicutilities,CoreWarssimulators). Withoutthebootstrap,theagentspendsits
21


# Page 22

Taskinstruction
Envbootstrap
pwd,files,languages,
pkgmanagers,memory
Initialprompt
task+snapshot
Agentloop
nativetoolcalling
30KBoutputcap
fail
Multi-perspective
completionchecklist
pass
Taskcomplete
Figure9: DiscoveredTerminalBench-2harness. TheharnessinheritsTerminus-KIRA’sna-
tivetoolcalling,outputcap,andcompletionchecklist(green). The environmentbootstrap
(red)isthecomponentdiscoveredbyMeta-Harness: itgathersasandboxsnapshotbefore
theagentloopbegins,eliminatingearlyexploratoryturns.
first2–4turnsprobingtheenvironment;ontaskswithtightturnbudgetsorwhereearly
wrongassumptionscascade,thosewastedturnscanbethedifferencebetweenpassandfail.
Thissuggeststhatthebootstrap’svalueislargestwhentheenvironmentisnon-obvious,
andthetaskrequirestheagenttomatchitsstrategytowhatisactuallyinstalled.
C DatasetDetails
C.1 OODTextClassificationDatasets
• SciCiteisa3-waycitation-intentclassificationbenchmarkintroducedbyCohanetal.
[14]. Eachexampleconsistsofacitationcontextfromascientificpaper,labeledbythe
citation’srhetoricalrole,suchasbackground,method,orresult. Thetasktestswhethera
modelcaninferwhyonepapercitesanotherfromthelocalscientificcontext.
• FiNER-139isafinancialnumericentityrecognitionbenchmarkintroducedbyLoukas
etal.[29].Itconsistsofword-levelannotationsfromfinancialfilingswith139fine-grained
XBRLentitytypes, makingitsubstantiallymorefine-grainedthanstandardsentence-
levelclassificationtasks. Thebenchmarktestswhetheramodelcanidentifyandclassify
numericfinancialentitiesfromcontext.
• AmazonReviewsistheEnglishportionoftheMultilingualAmazonReviewsCorpus
introduced by Keung et al. [22]. In our setting, it is used as a 5-way review rating
predictiontask,wherethelabelcorrespondstothereview’sstarrating. Thisbenchmark
evaluatesgeneral-domainsentimentandratingpredictionfromproductreviewtext.
• FinancialPhraseBankisa3-wayfinancialsentimentbenchmarkintroducedbyMalo
etal.[32]. Itconsistsofsentencesfromfinancialnewsandrelatedeconomictextlabeled
22


# Page 23

aspositive, neutral, ornegativewithrespecttomarketsentiment. Thetaskevaluates
domain-specificsentimentclassificationinfinance.
• GoEmotionsisafine-grainedemotionclassificationbenchmarkintroducedbyDemszky
etal.[15]. ItcontainsEnglishRedditcommentsannotatedwith27emotioncategories
plus a neutral category, and is commonly treated as a 28-way classification task. The
benchmarktestsnuancedaffectrecognitionbeyondcoarsepositive-negativesentiment.
• Banking77isafine-grainedintentclassificationbenchmarkintroducedbyCasanueva
etal.[11]. Itcontainsonlinebankinguserutteranceslabeledwith77intents,covering
a wide range of customer service requests. The task evaluates single-domain intent
detectionwithalargelabelspace.
• AG News is a 4-way news topic classification benchmark commonly associated with
thetextclassificationsetupofZhangetal.[60]. Examplesarelabeledwithbroadnews
categories such as world, sports, business, and science/technology. It is a standard
general-domainbenchmarkfortopicclassification.
• SciTailisascience-domaintextualentailmentbenchmarkinwhichthetaskistopredict
whetherahypothesisisentailedbyapremisesentenceinascience-focusedinference
setting[24].
• TweetEval(Hate)isthehate-speechsubsetoftheTweetEvalbenchmarkintroducedby
Barbieri et al. [7]. It is a binary tweet classification task for detecting hateful versus
non-hatefulcontentwithinaunifiedsocial-mediaevaluationsuite. Thisbenchmarktests
robustclassificationinnoisy,short-formsocialmediatext.
C.2 MathRetrievalCorpus
Table 10 lists the datasets composing the retrieval corpus used in Section 4.2. The raw
sourcescontainmoreproblemsthanthefinalcorpus;severalfilteringstepswereapplied
beforemerging. NuminaMath-1.5wasfilteredtocompetition-mathsubsets(AMC/AIME,
olympiadreferences,numbertheory,inequalities,andrelatedsources),discardinglower-
qualityweb-scrapedentries. OpenMathReasoningwasdeduplicatedtoonesolutionper
problem(retainingthesolutionwiththehighestpassrateonanindependentverifier),and
problemswhosesourcematchedanyevaluationbenchmarkfamily(IMO,AIME,HMMT,
SMT,USAMO,Putnam)wereremovedbeforededuplication. Theentirecorpuswasthen
decontaminatedagainstallevaluationbenchmarksandthesearchsetusedduringharness
search,usingexactprefixmatchingfollowedbyfuzzyJaccardsimilarity(threshold0.8);any
corpusproblemmatchinganevalproblemundereithercriterionwasdiscarded. Solutions
fromOpenMathReasoningandDeepMatharetruncatedto5,000characterstolimitretrieval
contextlength. Atruntime,theselectedharnessfurtherrestrictsretrievaltoentrieswith
non-emptysolutionsshorterthan4,000characters. Retrievedsolutionsaretruncatedagain
to 3,000 characters when inserted into the prompt. For the geometry route, the harness
alsoconstructsaseparatehard-referenceindexfromNuminaMathproblemswithdifficulty
greaterthan6.
C.3 MathIMO-levelTestSet
The main text aggregates results over 200 IMO-level problems drawn from IMO-
AnswerBench, IMO-ProofBench, ArXivMath December 2025, and ArXivMath January
2026. The200-problemevaluationsetconsistsofastratified100-problemsubsetofIMO-
AnswerBench, together with all problems from the other three benchmarks. This per-
benchmark breakdown is useful because the four datasets mix answer-style, proof, and
research-styleproblems,whichareaggregatedtogetherinthemainpaperforbrevity. When
included,thetableinthissectionshouldreporteachbenchmarkseparatelyforbothBase
andMeta-Harnessacrossthefiveheld-outmodels.
23


# Page 24

Dataset Problems Sol. Len Proof
OpenMathReasoning 281,743 5,000† 34%
DeepMath-103K 103,021 5,000† 0%
NuminaMath-1.5 129,520 1,376 13%
PolyMath 11,083 363 0%
Omni-MATH 4,289 829 0%
FineProofs-SFT 4,275 3,977 100%
AIME1983–2024 933 — 0%
Putnam-AXIOM 492 888 100%
Total 535,356 5,000† 22%
†Truncatedat5,000characters;actualsolutionsarelonger.
Table 10: Datasets in the math retrieval corpus (535K problems total). Sol. Len is the
mediansolutionlengthincharacters. Proofindicateswhetherthedatasetcontainsproof-
typeproblems(byanswerorproblemtypefield).
Dataset Problems
IMO-AnswerBench 100
IMO-ProofBench 60
ArXivMathDec.2025 17
ArXivMathJan.2026 23
Total 200
Table11: Breakdownofthe200-problemIMO-levelevaluationset.
D PracticalImplementationTips
Meta-Harness is largely domain-agnostic: we expect it to apply in any setting where a
language model is wrapped by a task-specific harness. Applying it in a new domain,
however,requiresoperatinginarelativelynewregimeofLLM-assistedcoding,wherethe
proposerconditionsonlong-horizonhistoriesofpriorrunsandwritesprogramswhose
effectsmayonlybecomevisiblemanystepslater. Ingettingthisworkflowtoworkreliably,
wefoundasmallsetofpracticalchoicesthatmatteredconsistentlyacrossthethreedomains
studiedinthispaper. Theguidelinesbelowarenotthemselvesscientificclaimsaboutthe
method; theyare engineeringlessonsfrombuilding andrunning the system, whichwe
hopewillmakeiteasierforfutureworktoapplyMeta-Harnessinotherdomains.
• Writeagoodskill. Theskilltextistheprimaryinterfaceforsteeringthesearch,andits
qualityisthestrongestleveronwhethertheloopworks. Theproposerreceivesanatural-
languageskill[5]thatdefinesitsrole,thedirectorylayout,CLIcommands,andoutput
format. Inpractice,theskillshouldconstrainoutputsandsafety-relevantbehavior,not
theproposer’sdiagnosisprocedure: itshouldspecifywhatisforbidden,whatartifactsto
produce,andwhatobjectivestooptimize,whileleavingthemodelfreetoinspectscores,
traces,andpriorcodeasneeded. OurintuitionfrominspectinglogsfromMeta-Harness
runsisthatafterenoughiterations,theaccumulatedtracesoftenshapetheproposer’s
behavior more than the skill itself. In our experience, iterating on the skill text had a
largereffectonsearchqualitythanchangingiterationcountorpopulationsize. Expectto
runafewshortevolutionruns(3–5iterationseach)specificallytodebugandrefinethe
skillbeforecommittingtoafullrun.
• Startwithabaselineharnessandasearchsetthatishardforit. Writeasimplebaseline
(e.g.,few-shotprompting),thenconstructthesearchsetbyeitherfilteringforexamples
that the baseline gets wrong or selecting a diverse subset of difficult instances. The
searchhaslittletooptimizeifthebaselinealreadysaturatestheevaluation. Keepthe
searchsetsmallenoughforroughly50fullevaluationsperrun(50–100examplesinour
24


# Page 25

classificationexperiments,88problemsformathretrieval);afast,discriminativeevalis
morevaluablethanalargeone.
• Logeverythinginaformatthatiseasytonavigate. Evaluationcodeshouldwritecode,
scores,andexecutiontracesinaformthattheproposercanqueryreliably.Inpractice,this
meansusingmachine-readableformatssuchasJSON,organizingartifactshierarchically,
choosingreasonableandconsistentfilenames,andadoptingnamingschemesthatmake
simpletoolssuchasregexsearchworkwell.
• MakelogsqueryablethroughasmallCLI(optional,buthelpful). Eachharnessgetsa
directorycontainingsourcecode,scores,andexecutiontraces,butasthehistorygrows,
raw filesystem access alone becomes cumbersome. A short CLI that lists the Pareto
frontier, shows top-k harnesses, and diffs code and results between pairs of runs can
maketheexperiencestoremucheasiertouse,andqueryingsuchCLIsiscloselyaligned
withtheworkflowsonwhichcodingagentsaretrained. Ifrelevantofflineexperience
exists(rolloutsfromothermodels,solvedproblemcorpora,relevantpapers),converting
itintothesamedirectorystructurecanalsohelpwarm-startexplorationandgroundnew
ideas. Thislayerhelpstheproposersavetokensitmayhavewastedonnavigation.
• Lightweight validation before expensive benchmarks. Write a small validation test
thatimportsthemodule,instantiatestheclass,andcallsbothmethodsonatinysetof
examples. Harnessesproposedduringthesearchshouldpassthistestbeforebeingfully
evaluated. Asimpletestscriptcancatchmostmalformedornonfunctionalcandidatesin
secondsandkeepthecostoffailuresnearzero.
• Automateevaluationoutsidetheproposer. Runningevalsissimpleenoughthatitisnot
worthmakingtheproposerdoit. Aseparateharnessshouldscorecandidatesandwrite
resultstothefilesystem.
E ExtendedRelatedWork
ThisappendixexpandsthebriefdiscussioninSection2andsituatesMeta-Harnessrelative
toseveralneighboringlinesofworkthatwecouldnotcoverindetailinthemaintext. A
recurringdistinctionisthatMeta-Harnessoptimizesexecutableharnessimplementations
andprovidestheproposerwithselectiveaccesstopriorcode,scores,andexecutiontraces
viathefilesystem.
AlphaEvolve / OpenEvolve. AlphaEvolve [35] and OpenEvolve [43] evolve code via
LLM-guidedmutationswithstructuredfeedback: theproposerreceivesaprogramdatabase
withscalarscores(4–22Ktokensperstep; Table1)andappliesfixedmutationstrategies
totournament-selectedparents. Thesemethodsaredesignedforalgorithmdiscoveryand
optimization(mathematicalconjectures,schedulingheuristics,hardwarekernels),where
thesearchtargetisasinglestatelessfunctionwithacleanscalarobjective,andmutations
arelocal. Harnessengineeringisadifferentregime: harnessesarestatefulprogramsthat
accumulateexperienceacrossmanyexamples,andasingledesignchoice(e.g.,whattostore
inmemory)cancascadethroughanentireevaluationsequence. Meta-Harnessaddresses
thisbygivinganunstructuredcodingagentfullfilesystemaccess,lettingitselectivelyread
anypriorcandidate’ssourcecode,executiontraces,andscores.
GEPA. GEPA [1] is the closest text optimizer in terms of feedback richness, providing
rollouttracespercandidate. Itisdesignedforpromptoptimizationontaskswithshort
feedback loops (math problems, instruction-following, code optimization), where each
rollout is a single LLM call or a short pipeline. In this regime, per-candidate reflection
workswell: oneprompt,oneanswer,onescore. Harnessengineeringrequiresreasoning
acrossmanyexamplesandmanycandidatessimultaneously:understandingwhyaretrieval
strategy works for one class of problems but degrades on another requires comparing
executiontracesacrossthefullpopulation. GEPAoperatesononecandidateatatime(2–8K
tokensperstep;Table1),withafixedcritiqueformatthatmustanticipatewhatinformation
isrelevant. Meta-Harnessgivestheproposeraccesstoallpriorcandidatessimultaneously
andletstheagentdecidewhattoexamine.
25


# Page 26

Promptorchestrationframeworks. Severalsystemsprovidestructuredabstractionsfor
composingmulti-stageLLMprograms. LMQL[8],LangChain[13],andDSPy[23]make
promptengineeringmoresystematicbyprovidinghigher-levelinterfacesforprompttem-
plates,controlflow,andmodularLLMpipelines. Theseframeworkshelpdevelopersspecify
and organize LLM programs, but they still typically require manual design of retrieval
policies,memoryupdates,andorchestrationlogic. Meta-Harnessoperatesatadifferent
level: itsearchesovertheimplementationofthesepoliciesinexecutablecode,treatingthe
harnessitselfastheoptimizationtarget.
26

