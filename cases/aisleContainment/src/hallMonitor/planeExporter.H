#include <sstream>
#include <limits>
class PlaneExporter {
 struct Plane { std::string name; int n0,n1; double interval,next; Foam::labelList ids; Foam::scalarField old; };
 std::vector<Plane> planes_; const Foam::fvMesh& mesh_; Foam::fileName out_; double oldTime_; bool enabled_,first_;
 void emit(Plane& a,double time,const Foam::scalarField& data) {
  Foam::scalarField values(data);Foam::reduce(values,Foam::sumOp<Foam::scalarField>());
  if(Foam::Pstream::master()){
   std::ostringstream nm;nm<<a.name<<"_"<<std::setw(6)<<std::setfill('0')<<int(std::round(time/a.interval))<<".bin";
   std::ofstream f((out_/nm.str()).c_str(),std::ios::binary); f.write(reinterpret_cast<const char*>(&time),8);
   std::vector<float> fields(a.n0*a.n1*4);std::vector<unsigned char> mask(a.n0*a.n1);
   for(int i=0;i<a.n0*a.n1;i++){double count=values[5*i+4];mask[i]=count>0;for(int k=0;k<4;k++)fields[4*i+k]=count>0?values[5*i+k]/count:std::numeric_limits<float>::quiet_NaN();}
   f.write(reinterpret_cast<const char*>(fields.data()),fields.size()*4);f.write(reinterpret_cast<const char*>(mask.data()),mask.size());
  }
 }
public:
 PlaneExporter(const Foam::fvMesh& mesh,bool enabled):mesh_(mesh),out_(mesh.time().globalPath()/"analysis/planes_raw"),oldTime_(mesh.time().value()),enabled_(enabled),first_(true){
  if(!enabled)return;
  if(Foam::Pstream::master())Foam::mkDir(out_);
  for(int a=0;a<6;a++){
   Plane p;p.name=a==0?"plan":a==1?"plan1m":a==2?"acrossMid":a==3?"acrossEnd":a==4?"alongCold":"acrossFall";p.n0=a==4?325:313;p.n1=a<2?325:65;p.interval=(a==0||a==2||a==5)?.125:.5;p.next=(std::floor((oldTime_+1e-8)/p.interval)+1)*p.interval;
   p.ids.setSize(p.n0*p.n1,-1);p.old.setSize(p.n0*p.n1*5,0);
   for(int i=0;i<p.n0;i++)for(int j=0;j<p.n1;j++){
    Foam::point c(a==4?5.4:.05*i,a<2?.05*j:a==4?.05*i:a==2?8.1:a==5?6.8:2.4,a<2?a==0?2.:1.:.05*j);
    bool solid=((c.y()<=.9||c.y()>=15.3)&&c.z()<=1.95);
    for(int k=0;k<3;k++)for(double x:{4.8*k+1.2,4.8*k+3.6})if(c.x()>=x-1e-9&&c.x()<=x+1.2+1e-9&&c.y()>=2.1-1e-9&&c.y()<=14.1+1e-9&&c.z()>=0-1e-9&&c.z()<=2.2+1e-9)solid=true;
    if(solid)continue;
    for(int k=0;k<3;k++)c[k]=Foam::max(Foam::scalar(1e-7),Foam::min(c[k],Foam::scalar(k==0?15.6-1e-7:k==1?16.2-1e-7:3.2-1e-7)));
    Foam::label id=mesh.findCell(c);int n=i*p.n1+j;p.ids[n]=id;if(id>=0){p.old[5*n]=293.15;p.old[5*n+4]=1;
     if(oldTime_>0 && mesh.foundObject<Foam::volScalarField>("T") && mesh.foundObject<Foam::volVectorField>("U")){
      p.old[5*n]=mesh.lookupObject<Foam::volScalarField>("T")[id];for(int q=0;q<3;q++)p.old[5*n+1+q]=mesh.lookupObject<Foam::volVectorField>("U")[id][q];
     }
    }
   }
   planes_.push_back(std::move(p));
  }
 }
 void execute(){
  if(!enabled_)return;
  double time=mesh_.time().value(); const auto& T=mesh_.lookupObject<Foam::volScalarField>("T");const auto& U=mesh_.lookupObject<Foam::volVectorField>("U");
  for(auto& a:planes_){
   Foam::scalarField now(a.old.size(),0);
   forAll(a.ids,i)if(a.ids[i]>=0){now[5*i]=T[a.ids[i]];for(int k=0;k<3;k++)now[5*i+1+k]=U[a.ids[i]][k];now[5*i+4]=1;}
   if(first_&&oldTime_==0)emit(a,0,a.old);
   
   while(a.next<=time+1e-9){double fraction=(a.next-oldTime_)/(time-oldTime_+1e-30);Foam::scalarField values(a.old+fraction*(now-a.old));emit(a,a.next,values);a.next+=a.interval;}
   a.old=std::move(now);
  }
  oldTime_=time;first_=false;
 }
};
