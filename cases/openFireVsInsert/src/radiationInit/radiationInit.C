/* Radiation alone on a fixed temperature field: the solved runs' starting radiation. It reads T
   and system/calibrationConfig (target W, iterations, earlyStop, isothermal), builds the case's
   radiation model, and calls its correct() `iterations` times, advancing the time by one step each
   call, printing each patch's absorbed power and the largest change from the call before; with
   earlyStop it stops once that change is under 0.2% of the target. It writes the patches' powers
   (postProcessing/radiation.csv, radiation_iterations.csv), every boundary face's qr
   (radiation_faces.csv), and the ray fields, G and qr at the final time. No air moves and nothing
   else is solved. The cloud study's rad84, the same source.                                    */
#include "fvCFD.H"
#include "radiationModel.H"
#include <fstream>
int main(int argc,char *argv[])
{
 #include "setRootCase.H"
 #include "createTime.H"
 #include "createMesh.H"
 volScalarField T(IOobject("T",runTime.timeName(),mesh,IOobject::MUST_READ,IOobject::AUTO_WRITE),mesh);
 autoPtr<radiation::radiationModel> rad(radiation::radiationModel::New(T));
 IOdictionary config(IOobject("calibrationConfig",runTime.system(),mesh,IOobject::MUST_READ,IOobject::NO_WRITE));
 const scalar target=config.get<scalar>("target");const label iterations=config.getOrDefault<label>("iterations",8);const bool iso=config.getOrDefault<bool>("isothermal",false);const bool early=config.getOrDefault<bool>("earlyStop",true);
 scalarList previous(mesh.boundaryMesh().nNonProcessor(),GREAT);
 std::ofstream history;if(Pstream::master()){mkDir(runTime.globalPath()/"postProcessing");history.open((runTime.globalPath()/"postProcessing"/"radiation_iterations.csv").c_str());history<<"iteration,patch,power_W,change_W\n";}
 for(label iter=0;iter<iterations;++iter){++runTime;rad->correct();const auto& flux=mesh.lookupObject<volScalarField>("qr");scalar maxChange=0,maxFlux=0;
 for(label b=0;b<mesh.boundaryMesh().nNonProcessor();++b){scalar q=gSum(flux.boundaryField()[b]*mesh.magSf().boundaryField()[b]);maxChange=max(maxChange,mag(q-previous[b]));previous[b]=q;maxFlux=max(maxFlux,gMax(mag(flux.boundaryField()[b])));if(Pstream::master())history<<iter+1<<","<<mesh.boundary()[b].name()<<","<<q<<","<<maxChange<<"\n";}
 Info<<"PATCH_POWER_ITERATION "<<iter+1<<" max_change_W "<<maxChange<<" max_abs_qr "<<maxFlux<<endl;
 if(early&&iter>0&&maxChange<.002*target&&(!iso||maxFlux<.5))break;
 }
 const auto& qr=mesh.lookupObject<volScalarField>("qr");
 if(Pstream::master()) mkDir(runTime.globalPath()/"postProcessing");
 std::ofstream f; if(Pstream::master())f.open((runTime.globalPath()/"postProcessing"/"radiation.csv").c_str());
 if(Pstream::master())f<<"patch,area_m2,power_absorbed_W,max_abs_qr_W_m2\n";
 for(label b=0;b<mesh.boundaryMesh().nNonProcessor();++b){scalar A=gSum(mesh.magSf().boundaryField()[b]);scalar q=gSum(qr.boundaryField()[b]*mesh.magSf().boundaryField()[b]);scalar mx=gMax(mag(qr.boundaryField()[b]));if(Pstream::master())f<<mesh.boundary()[b].name()<<","<<A<<","<<q<<","<<mx<<"\n";}
 std::ofstream samples; if(Pstream::master())samples.open((runTime.globalPath()/"postProcessing"/"radiation_faces.csv").c_str()); if(Pstream::master())samples<<"patch,x,y,z,area_m2,qr_W_m2\n";
 for(label b=0;b<mesh.boundaryMesh().nNonProcessor();++b){List<scalarList> data(Pstream::nProcs());auto& mine=data[Pstream::myProcNo()];mine.setSize(mesh.boundary()[b].size()*5);forAll(mesh.boundary()[b],j){vector c=mesh.Cf().boundaryField()[b][j];for(label d=0;d<3;++d)mine[j*5+d]=c[d];mine[j*5+3]=mesh.magSf().boundaryField()[b][j];mine[j*5+4]=qr.boundaryField()[b][j];} Pstream::gatherList(data);if(Pstream::master())for(const auto& part:data)for(label j=0;j<part.size()/5;++j){samples<<mesh.boundary()[b].name();for(label d=0;d<5;++d)samples<<","<<part[j*5+d];samples<<"\n";}}
 runTime.writeNow(); Info<<"End"<<endl;return 0;
}
